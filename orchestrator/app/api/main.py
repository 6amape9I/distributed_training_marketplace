from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from orchestrator.app.api.routes.artifacts import router as artifacts_router
from orchestrator.app.api.routes.evaluator_tasks import router as evaluator_tasks_router
from orchestrator.app.api.routes.health import router as health_router
from orchestrator.app.api.routes.internal import router as internal_router
from orchestrator.app.api.routes.jobs import router as jobs_router
from orchestrator.app.api.routes.nodes import router as nodes_router
from orchestrator.app.api.routes.rounds import router as rounds_router
from orchestrator.app.api.routes.status import router as status_router
from orchestrator.app.api.routes.trainer_tasks import router as trainer_tasks_router
from orchestrator.app.infrastructure.blockchain.client import TrainingMarketplaceClient
from orchestrator.app.infrastructure.container import AppContainer, create_container
from orchestrator.app.infrastructure.db.session import database_is_available
from orchestrator.app.infrastructure.settings import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    container: AppContainer = app.state.container
    database_is_available(container.engine)
    yield


def create_app(
    settings: Settings | None = None,
    blockchain_client: TrainingMarketplaceClient | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    container = create_container(resolved_settings, blockchain_client=blockchain_client)
    app = FastAPI(
        title="distributed-training-marketplace-orchestrator",
        version="0.5.0",
        lifespan=lifespan,
    )
    app.state.container = container
    app.include_router(health_router)
    app.include_router(status_router)
    app.include_router(artifacts_router)
    app.include_router(jobs_router)
    app.include_router(rounds_router)
    app.include_router(nodes_router)
    app.include_router(trainer_tasks_router)
    app.include_router(evaluator_tasks_router)
    app.include_router(internal_router)
    return app
