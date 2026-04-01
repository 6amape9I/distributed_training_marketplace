from fastapi import FastAPI

from orchestrator.app.api.routes.health import router as health_router
from orchestrator.app.api.routes.jobs import router as jobs_router
from orchestrator.app.api.routes.nodes import router as nodes_router


def create_app() -> FastAPI:
    app = FastAPI(title="distributed-training-marketplace-orchestrator", version="0.1.0")
    app.include_router(health_router)
    app.include_router(jobs_router)
    app.include_router(nodes_router)
    return app


app = create_app()
