from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from evaluator_agent.app.api.routes import router as evaluator_router
from evaluator_agent.app.application.runtime import EvaluatorRuntime
from evaluator_agent.app.execution.evaluation_executor import EvaluationExecutor
from evaluator_agent.app.orchestrator_client.client import OrchestratorClient
from evaluator_agent.app.settings import EvaluatorSettings, get_settings
from evaluator_agent.app.storage.workspace import LocalWorkspace


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime: EvaluatorRuntime = app.state.runtime
    runtime.start()
    try:
        yield
    finally:
        runtime.stop()


def create_app(
    settings: EvaluatorSettings | None = None,
    orchestrator_client: OrchestratorClient | None = None,
    runtime: EvaluatorRuntime | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_runtime = runtime or EvaluatorRuntime(
        settings=resolved_settings,
        orchestrator_client=orchestrator_client or OrchestratorClient(resolved_settings.orchestrator_base_url),
        executor=EvaluationExecutor(),
        workspace=LocalWorkspace(Path(resolved_settings.local_workspace_path)),
    )
    app = FastAPI(title=resolved_settings.service_name, version="0.4.0", lifespan=lifespan)
    app.state.runtime = resolved_runtime
    app.include_router(evaluator_router)
    return app
