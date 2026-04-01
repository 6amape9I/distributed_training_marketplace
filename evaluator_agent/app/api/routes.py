from __future__ import annotations

from fastapi import APIRouter, Request

from evaluator_agent.app.application.runtime import EvaluatorRuntime

router = APIRouter(tags=["evaluator"])


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    runtime: EvaluatorRuntime = request.app.state.runtime
    return {"status": "ok", "service": runtime.settings.service_name}


@router.get("/status")
def status(request: Request) -> dict[str, object]:
    runtime: EvaluatorRuntime = request.app.state.runtime
    return runtime.status_payload()
