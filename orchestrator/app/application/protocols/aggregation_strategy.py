from collections.abc import Sequence
from typing import Protocol

from shared.python.schemas import ArtifactRef


class AggregationStrategy(Protocol):
    def aggregate(self, artifacts: Sequence[ArtifactRef]) -> ArtifactRef: ...
