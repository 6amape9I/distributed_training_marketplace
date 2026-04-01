from enum import StrEnum


class ArtifactKind(StrEnum):
    MODEL_INPUT = "model_input"
    DATASET_MANIFEST = "dataset_manifest"
    TASK_RESULT = "task_result"
    TRAINER_REPORT = "trainer_report"
