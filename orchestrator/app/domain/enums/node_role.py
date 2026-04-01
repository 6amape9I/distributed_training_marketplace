from enum import StrEnum


class NodeRole(StrEnum):
    TRAINER = "trainer"
    EVALUATOR = "evaluator"
