"""Provision a local API-key grant; emit the secret once, store only its hash.
Usage: uv run python scripts/provision_api_key.py --tenant vesta
The operator must separately declare additional tenants in QA_TENANTS_FILE.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant", default="vesta")
    parser.add_argument("--file", type=Path, default=Path(".qa-secrets/api-keys.json"))
    parser.add_argument(
        "--scope",
        action="append",
        choices=["reviews:read", "reviews:write", "feedback:read", "feedback:write", "skills:read", "skills:write"],
    )
    args = parser.parse_args()
    grants = json.loads(args.file.read_text()) if args.file.exists() else []
    if not isinstance(grants, list):
        raise SystemExit("Key file must contain a JSON array.")
    secret = "qak_" + secrets.token_urlsafe(32)
    grants.append(
        {
            "key_sha256": hashlib.sha256(secret.encode()).hexdigest(),
            "tenant_id": args.tenant,
            "scopes": args.scope
            or ["reviews:read", "reviews:write", "feedback:read", "feedback:write"],
        }
    )
    args.file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=args.file.parent, delete=False
    ) as temp:
        json.dump(grants, temp, indent=2)
        temp.write("\n")
        temp.flush()
        os.fsync(temp.fileno())
        os.chmod(temp.name, 0o600)
    os.replace(temp.name, args.file)
    print("API key (shown once; keep secret):")
    print(secret)
    print(f"Hashed grant saved for {args.tenant} in {args.file}.")


if __name__ == "__main__":
    main()
