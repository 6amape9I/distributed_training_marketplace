from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class EvaluatorSettings:
    service_name: str = "evaluator-agent"
