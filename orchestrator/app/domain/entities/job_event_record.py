from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True, frozen=True)
class JobEventRecord:
    event_name: str
    transaction_hash: str
    log_index: int
    block_number: int
    job_id: int | None
    payload: dict[str, Any]
    processed_at: datetime | None = None
