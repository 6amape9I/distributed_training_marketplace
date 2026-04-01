from dataclasses import dataclass


@dataclass(slots=True)
class PlaceholderOrchestrationService:
    name: str = "stage1-scaffold"

    def describe(self) -> str:
        return "Orchestrator business logic starts in Stage 2."
