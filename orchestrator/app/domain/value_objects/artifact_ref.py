from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ArtifactRefValue:
    uri: str
    digest: str | None = None
