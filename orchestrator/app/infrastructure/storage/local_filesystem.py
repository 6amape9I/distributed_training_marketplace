from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class LocalFilesystemStorage:
    root: Path

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, *, artifact_id: str, name: str, payload: bytes) -> Path:
        artifact_dir = self.root / artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(name).name
        destination = artifact_dir / safe_name
        destination.write_bytes(payload)
        return destination.relative_to(self.root)

    def load_bytes(self, relative_path: Path) -> bytes:
        return (self.root / relative_path).read_bytes()
