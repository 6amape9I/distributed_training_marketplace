from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class LocalFilesystemStorage:
    root: Path
