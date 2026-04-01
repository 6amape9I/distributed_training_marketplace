from typing import Annotated

from fastapi import APIRouter, Depends

from orchestrator.app.api.deps import get_status_service
from orchestrator.app.application.dto import StatusResponse
from orchestrator.app.application.services import StatusService

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
def status(
    status_payload: Annotated[tuple[StatusService, int | None], Depends(get_status_service)],
) -> StatusResponse:
    service, last_processed_block = status_payload
    return StatusResponse(**service.get_status(last_processed_block))
