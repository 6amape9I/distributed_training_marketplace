from enum import StrEnum


class RoundStatus(StrEnum):
    PENDING = "pending"
    SEEDED = "seeded"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
