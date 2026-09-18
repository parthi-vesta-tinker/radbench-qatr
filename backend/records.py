"""Private persistence records, independent of public response models."""
from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class AcceptedSnapshot:
    tenant_id: str
    id: str
    sha256: str
    config: str

    @classmethod
    def from_row(cls, row) -> "AcceptedSnapshot":
        return cls(**{name: row[name] for name in cls.__dataclass_fields__})

    def decode(self) -> dict:
        if hashlib.sha256(self.config.encode()).hexdigest() != self.sha256:
            raise ValueError("Accepted snapshot integrity failure")
        value = json.loads(self.config)
        if not isinstance(value, dict):
            raise ValueError("Accepted snapshot must be an object")
        return value
