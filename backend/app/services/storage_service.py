from pathlib import Path
from typing import Protocol
from ..config import settings

class Storage(Protocol):
    def save(self, key: str, data: bytes) -> str: ...
    def path(self, key: str) -> str: ...
    def delete(self, key: str) -> None: ...

class LocalStorage:
    """Swap for an S3/GCS class implementing the same Protocol."""
    def __init__(self, root: str):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def save(self, key: str, data: bytes) -> str:
        p = self.root / key; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        return key
    def path(self, key: str) -> str:
        return str(self.root / key)
    def delete(self, key: str) -> None:
        (self.root / key).unlink(missing_ok=True)

storage: Storage = LocalStorage(settings.storage_dir)
