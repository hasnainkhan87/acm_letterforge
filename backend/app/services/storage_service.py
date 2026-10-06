from pathlib import Path
from typing import Protocol
from ..config import settings

class Storage(Protocol):
    def save(self, key: str, data: bytes) -> str: ...
    def path(self, key: str) -> str: ...
    def delete(self, key: str) -> None: ...

class LocalStorage:
    """Files live only under STORAGE_DIR. Swap for an S3/GCS class implementing the same Protocol."""
    SUBDIRS = ("templates", "signatures", "generated")

    def __init__(self, root: str):
        self.root = Path(root).resolve(); self.root.mkdir(parents=True, exist_ok=True)
        for d in self.SUBDIRS: (self.root / d).mkdir(exist_ok=True)  # never touches existing contents

    def _safe(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if p != self.root and self.root not in p.parents:  # blocks ../ and absolute-path tricks
            raise ValueError("Invalid storage key")
        return p

    def save(self, key: str, data: bytes) -> str:
        p = self._safe(key); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        return key

    def path(self, key: str) -> str:
        return str(self._safe(key))

    def delete(self, key: str) -> None:
        self._safe(key).unlink(missing_ok=True)

storage: Storage = LocalStorage(settings.storage_dir)
