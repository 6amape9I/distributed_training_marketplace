from __future__ import annotations

from fastapi import APIRouter, Request

from trainer_agent.app.application.runtime import TrainerRuntime

router = APIRouter(tags=["trainer"])


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    runtime: TrainerRuntime = request.app.state.runtime
    return {"status": "ok", "service": runtime.settings.service_name}


@router.get("/status")
def status(request: Request) -> dict[str, object]:
    runtime: TrainerRuntime = request.app.state.runtime
    return runtime.status_payload()
