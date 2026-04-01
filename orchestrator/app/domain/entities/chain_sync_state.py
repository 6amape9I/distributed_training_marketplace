from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ChainSyncState:
    sync_key: str
    chain_id: int
    contract_address: str
    last_processed_block: int
    updated_at: datetime | None = None
