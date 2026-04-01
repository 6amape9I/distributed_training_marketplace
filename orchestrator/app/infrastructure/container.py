from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from orchestrator.app.application.services.job_lifecycle_service import JobLifecycleService
from orchestrator.app.application.services.simple_node_selection_strategy import SimpleNodeSelectionStrategy
from orchestrator.app.infrastructure.blockchain.client import TrainingMarketplaceClient
from orchestrator.app.infrastructure.db.repositories import (
    SqlAlchemyJobEventRepository,
    SqlAlchemyJobRepository,
    SqlAlchemyNodeRepository,
    SqlAlchemySyncStateRepository,
)
from orchestrator.app.infrastructure.db.session import build_engine, build_session_factory
from orchestrator.app.infrastructure.settings import Settings


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    blockchain_client: TrainingMarketplaceClient
    lifecycle_service: JobLifecycleService
    node_selection_strategy: SimpleNodeSelectionStrategy

    def job_repository(self, session: Session) -> SqlAlchemyJobRepository:
        return SqlAlchemyJobRepository(session)

    def node_repository(self, session: Session) -> SqlAlchemyNodeRepository:
        return SqlAlchemyNodeRepository(session)

    def sync_state_repository(self, session: Session) -> SqlAlchemySyncStateRepository:
        return SqlAlchemySyncStateRepository(session)

    def job_event_repository(self, session: Session) -> SqlAlchemyJobEventRepository:
        return SqlAlchemyJobEventRepository(session)


def create_container(
    settings: Settings,
    blockchain_client: TrainingMarketplaceClient | None = None,
) -> AppContainer:
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        blockchain_client=blockchain_client
        or TrainingMarketplaceClient(
            rpc_url=settings.chain_rpc_url,
            contract_address=settings.marketplace_contract_address,
        ),
        lifecycle_service=JobLifecycleService(),
        node_selection_strategy=SimpleNodeSelectionStrategy(),
    )
