from collections.abc import Sequence
from typing import Protocol

from orchestrator.app.domain.entities import Artifact


class ArtifactRepository(Protocol):
    def get(self, artifact_id: str) -> Artifact | None: ...

    def list(self) -> Sequence[Artifact]: ...

    def list_by_task(self, task_id: str) -> Sequence[Artifact]: ...

    def upsert(self, artifact: Artifact) -> Artifact: ...
