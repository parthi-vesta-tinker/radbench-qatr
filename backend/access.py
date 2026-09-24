"""Tenant identity comes from server configuration or credentials, never the caller."""

from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SCOPES = frozenset({"reviews:read", "reviews:write", "feedback:read", "feedback:write", "skills:read", "skills:write", "settings:write"})
bearer = HTTPBearer(auto_error=False)


class AccessError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


@dataclass(frozen=True)
class Principal:
    tenant_id: str
    scopes: frozenset[str]
    actor_name: str | None = None


def tenants():
    path = os.environ.get("QA_TENANTS_FILE", "")
    entries = json.loads(Path(path).read_text(encoding="utf-8")) if path else {"vesta": {}}
    if not isinstance(entries, dict) or "vesta" not in entries:
        raise ValueError("Tenant configuration must include vesta.")
    for key, config in entries.items():
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", key) or not isinstance(
            config, dict
        ):
            raise ValueError("Invalid tenant configuration.")
        if set(config) - {"model", "policy_path", "skill_release"}:
            raise ValueError("Unknown tenant configuration field.")
        from .content import profile
        profile(key, config)
    return entries


def access_mode():
    mode = os.environ.get("ACCESS_MODE", "local")
    if mode not in ("local", "public", "api_key"):
        raise ValueError("ACCESS_MODE must be local, public or api_key.")
    return mode


def key_grants():
    path = os.environ.get("QA_TENANT_KEYS_FILE", "")
    if not path:
        raise ValueError("QA_TENANT_KEYS_FILE is required in api_key mode.")
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    known = tenants()
    seen = set()
    if not isinstance(records, list) or not records:
        raise ValueError("Configure at least one API key grant.")
    for row in records:
        digest = row.get("key_sha256", "")
        if (
            not re.fullmatch("[a-f0-9]{64}", digest)
            or digest in seen
            or row.get("tenant_id") not in known
        ):
            raise ValueError("Invalid API key grant.")
        if set(row) - {"key_sha256", "tenant_id", "scopes", "actor_name"}:
            raise ValueError("Unknown API key grant field.")
        actor_name = row.get("actor_name")
        if actor_name is not None and (
            not isinstance(actor_name, str) or not actor_name.strip() or len(actor_name) > 120
        ):
            raise ValueError("Invalid API key actor name.")
        if not isinstance(row.get("scopes"), list) or not set(row["scopes"]) <= SCOPES:
            raise ValueError("Invalid API key scopes.")
        seen.add(digest)
    return records


def validate_access_config():
    tenants()
    if access_mode() == "api_key":
        key_grants()


def principal(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
):
    mode = access_mode()
    if request.headers.get("X-Tenant-Id") is not None:
        raise AccessError(
            400,
            "TENANT_OVERRIDE_NOT_ALLOWED",
            "Tenant identity is determined by server configuration or credentials.",
        )
    if mode in ("local", "public"):
        if mode == "local" and (
            not request.client or request.client.host not in ("127.0.0.1", "::1")
        ):
            raise AccessError(
                403, "LOCAL_ACCESS_ONLY", "Local mode accepts loopback requests only."
            )
        if request.headers.get("Authorization"):
            raise AccessError(
                401, "AUTH_MODE_MISMATCH", "Bearer credentials require api_key mode."
            )
        actor_name = os.environ.get("QA_LOCAL_OPERATOR_NAME", "").strip() or None
        p = Principal("vesta", SCOPES, actor_name)
    else:
        if not credentials or credentials.scheme.lower() != "bearer":
            raise AccessError(
                401, "AUTHENTICATION_REQUIRED", "Provide a valid bearer API key."
            )
        digest = hashlib.sha256(credentials.credentials.encode()).hexdigest()
        row = next(
            (x for x in key_grants() if hmac.compare_digest(x["key_sha256"], digest)),
            None,
        )
        if row is None:
            raise AccessError(401, "INVALID_API_KEY", "Provide a valid bearer API key.")
        p = Principal(
            row["tenant_id"],
            frozenset(row["scopes"]),
            (row.get("actor_name") or "").strip() or None,
        )
    request.state.tenant_id = p.tenant_id
    return p


def require(scope):
    def dependency(p: Principal = Depends(principal)):
        if scope not in p.scopes:
            raise AccessError(
                403,
                "INSUFFICIENT_SCOPE",
                "This API key does not grant the required operation.",
            )
        return p

    return dependency
