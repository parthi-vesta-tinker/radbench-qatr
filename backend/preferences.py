"""Tenant runtime settings, stored atomically outside immutable review snapshots.

The sidecar is configuration, not a resource-store schema migration. Per-tenant file
locks serialize writers across local processes; revision checks reject stale saves.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from .access import AccessError, access_mode, tenants


class Features(BaseModel):
    model_config = ConfigDict(extra='forbid')
    playground: bool = True
    skills: bool = True
    classification: bool = False
    classification_analysis: bool = False


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int = Field(ge=0)
    run_mode: Literal['demo', 'live']
    core_model: str = Field(min_length=1, max_length=120)
    features: Features


class AppSettings(SettingsUpdate):
    access_mode: Literal['local', 'public', 'api_key']
    available_models: list[str]
    can_edit: bool
    openai_configured: bool
    classification_configured: bool


def location(tenant):
    from . import store
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', tenant):
        raise ValueError('Invalid settings tenant.')
    return store.DATA / 'settings' / (tenant + '.json')


def defaults(tenant):
    entry = tenants()[tenant]
    mode = os.environ.get('RUN_MODE', 'demo')
    if mode not in ('demo', 'live'):
        raise ValueError('RUN_MODE must be demo or live.')
    return SettingsUpdate(revision=0, run_mode=mode,
                          core_model=entry.get('model', os.environ.get('OPENAI_MODEL', '').strip()) or 'gpt-6-astra',
                          features=Features(classification=os.environ.get('QA_JEV_ENABLED', 'false').lower() == 'true'))


def allowed_models(tenant):
    base = defaults(tenant).core_model
    configured = os.environ.get('CORE_REVIEW_MODELS', '').strip()
    return list(dict.fromkeys(part.strip() for part in (configured or base).split(',') if part.strip()))


def read(tenant):
    path = location(tenant)
    if not path.exists():
        return defaults(tenant)
    return SettingsUpdate.model_validate_json(path.read_text(encoding='utf-8'))


def require_feature(tenant, feature):
    if not getattr(read(tenant).features, feature):
        raise AccessError(403, 'FEATURE_DISABLED', f'{feature.capitalize()} is disabled in Settings.')


def editable(principal):
    return access_mode() != 'public' and 'settings:write' in principal.scopes


def public(principal):
    value = read(principal.tenant_id)
    return AppSettings(**value.model_dump(), access_mode=access_mode(),
                       available_models=allowed_models(principal.tenant_id), can_edit=editable(principal),
                       openai_configured=bool(os.environ.get('OPENAI_API_KEY')),
                       classification_configured=bool(os.environ.get('TYPESAFE_API_KEY')) and access_mode() != 'public')


@contextmanager
def write_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_suffix('.lock'), 'a+b') as lock:
        if os.name == 'nt':
            import msvcrt
            if lock.tell() == 0:
                lock.write(b'0'); lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def save(principal, payload, *, server=False):
    if not server and not editable(principal):
        raise AccessError(403, 'INSUFFICIENT_SCOPE', 'Changing settings requires local access or settings:write credentials.')
    tenant = principal.tenant_id
    path = location(tenant)
    with write_lock(path):
        current = read(tenant)
        if current.revision != payload.revision:
            # A lost successful PUT response can be retried without a second update.
            retry = payload.model_copy(update={'revision': payload.revision + 1})
            if current == retry:
                return public(principal)
            raise AccessError(409, 'SETTINGS_CONFLICT', 'Settings changed elsewhere. Reload settings before saving.')
        if payload.core_model not in allowed_models(tenant):
            raise AccessError(422, 'MODEL_NOT_ALLOWED', 'Select a server-approved core review model.')
        if payload.run_mode == 'live' and not os.environ.get('OPENAI_API_KEY'):
            raise AccessError(422, 'MODEL_NOT_CONFIGURED', 'Configure OPENAI_API_KEY on the server before selecting Live.')
        if payload.features.classification and not os.environ.get('TYPESAFE_API_KEY'):
            raise AccessError(422, 'JEV_NOT_CONFIGURED', 'Configure TYPESAFE_API_KEY on the server before enabling classification.')
        saved = payload.model_copy(update={'revision': current.revision + 1})
        descriptor, name = tempfile.mkstemp(dir=path.parent, prefix='.settings-', suffix='.tmp')
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                stream.write(saved.model_dump_json()); stream.flush(); os.fsync(stream.fileno())
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)
        return public(principal)


def apply_launch_overrides(*, run_mode=None, core_model=None, classification=None):
    """Explicit local launcher flags update Vesta settings once, before serving requests."""
    from .access import Principal, SCOPES
    current = read('vesta')
    changes = {}
    if run_mode is not None:
        changes['run_mode'] = run_mode
    if core_model is not None:
        changes['core_model'] = core_model
    if classification is not None:
        changes['features'] = current.features.model_copy(update={'classification': classification})
    updated = current.model_copy(update=changes)
    if updated != current:
        save(Principal('vesta', SCOPES), updated, server=True)
