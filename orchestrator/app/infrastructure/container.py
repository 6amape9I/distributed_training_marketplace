from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from orchestrator.app.application.services.job_lifecycle_service import JobLifecycleService
from orchestrator.app.application.services.simple_node_selection_strategy import SimpleNodeSelectionStrategy
from orchestrator.app.infrastructure.blockchain.client import TrainingMarketplaceClient
from orchestrator.app.infrastructure.db.repositories import (
    SqlAlchemyArtifactRepository,
    SqlAlchemyJobEventRepository,
    SqlAlchemyJobRepository,
    SqlAlchemyNodeRepository,
    SqlAlchemySyncStateRepository,
    SqlAlchemyTrainingTaskRepository,
)
from orchestrator.app.infrastructure.db.session import build_engine, build_session_factory
from orchestrator.app.infrastructure.settings import Settings
from orchestrator.app.infrastructure.storage.local_filesystem import LocalFilesystemStorage


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    blockchain_client: TrainingMarketplaceClient
    lifecycle_service: JobLifecycleService
    node_selection_strategy: SimpleNodeSelectionStrategy
    artifact_storage: LocalFilesystemStorage

    def job_repository(self, session: Session) -> SqlAlchemyJobRepository:
        return SqlAlchemyJobRepository(session)

    def node_repository(self, session: Session) -> SqlAlchemyNodeRepository:
        return SqlAlchemyNodeRepository(session)

    def sync_state_repository(self, session: Session) -> SqlAlchemySyncStateRepository:
        return SqlAlchemySyncStateRepository(session)

    def job_event_repository(self, session: Session) -> SqlAlchemyJobEventRepository:
        return SqlAlchemyJobEventRepository(session)

    def training_task_repository(self, session: Session) -> SqlAlchemyTrainingTaskRepository:
        return SqlAlchemyTrainingTaskRepository(session)

    def artifact_repository(self, session: Session) -> SqlAlchemyArtifactRepository:
        return SqlAlchemyArtifactRepository(session)


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
        artifact_storage=LocalFilesystemStorage(Path(settings.artifact_root)),
    )
