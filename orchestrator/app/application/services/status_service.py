from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from orchestrator.app.infrastructure.blockchain import TrainingMarketplaceClient
from orchestrator.app.infrastructure.db.session import database_is_available
from orchestrator.app.infrastructure.settings import Settings
from sqlalchemy.engine import Engine


class StatusService:
    def __init__(self, *, settings: Settings, engine: Engine, blockchain: TrainingMarketplaceClient) -> None:
        self.settings = settings
        self.engine = engine
        self.blockchain = blockchain

    def get_status(self, last_processed_block: int | None) -> dict[str, object]:
        try:
            database_ok = database_is_available(self.engine)
            database_error = None
        except SQLAlchemyError as exc:
            database_ok = False
            database_error = str(exc)

        blockchain_status = self.blockchain.get_status()
        healthy = database_ok and blockchain_status["reachable"]
        return {
            "status": "ok" if healthy else "degraded",
            "database": {"reachable": database_ok, "error": database_error},
            "blockchain": blockchain_status,
            "configured_chain_id": self.settings.chain_id,
            "contract_address": self.settings.marketplace_contract_address,
            "last_processed_block": last_processed_block,
        }
