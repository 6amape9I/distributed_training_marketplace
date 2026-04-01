from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class LocalWorkspace:
    root: Path

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def write_task_file(self, evaluation_task_id: str, name: str, payload: bytes) -> Path:
        task_dir = self.root / evaluation_task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        destination = task_dir / Path(name).name
        destination.write_bytes(payload)
        return destination
