from typing import Protocol

from orchestrator.app.domain.entities import ChainSyncState


class SyncStateRepository(Protocol):
    def get(self, sync_key: str) -> ChainSyncState | None: ...

    def upsert(self, state: ChainSyncState) -> ChainSyncState: ...
