from __future__ import annotations

from pydantic import BaseModel, Field


class TrainerReport(BaseModel):
    task_id: str
    trainer_node_id: str
    data_partition_id: str
    sample_count: int = Field(ge=1)
    epochs: int = Field(ge=1)
    learning_rate: float = Field(gt=0)
    average_loss: float = Field(ge=0)
    accuracy: float = Field(ge=0, le=1)
    model_digest: str
