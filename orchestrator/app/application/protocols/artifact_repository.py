from typing import Protocol

from shared.python.schemas import ArtifactRef


class ArtifactRepository(Protocol):
    def put(self, name: str, payload: bytes) -> ArtifactRef: ...

    def get(self, ref: ArtifactRef) -> bytes: ...
