from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from trainer_agent.app.api.routes import router as trainer_router
from trainer_agent.app.application.runtime import TrainerRuntime
from trainer_agent.app.execution.local_fit_executor import LocalFitExecutor
from trainer_agent.app.orchestrator_client.client import OrchestratorClient
from trainer_agent.app.settings import TrainerSettings, get_settings
from trainer_agent.app.storage.workspace import LocalWorkspace


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime: TrainerRuntime = app.state.runtime
    runtime.start()
    try:
        yield
    finally:
        runtime.stop()



def create_app(
    settings: TrainerSettings | None = None,
    orchestrator_client: OrchestratorClient | None = None,
    runtime: TrainerRuntime | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_runtime = runtime or TrainerRuntime(
        settings=resolved_settings,
        orchestrator_client=orchestrator_client or OrchestratorClient(resolved_settings.orchestrator_base_url),
        executor=LocalFitExecutor(),
        workspace=LocalWorkspace(Path(resolved_settings.local_workspace_path)),
    )
    app = FastAPI(title=resolved_settings.service_name, version="0.3.0", lifespan=lifespan)
    app.state.runtime = resolved_runtime
    app.include_router(trainer_router)
    return app
