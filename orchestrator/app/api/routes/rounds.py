from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from orchestrator.app.api.deps import get_round_reconciliation_service
from orchestrator.app.application.dto import RoundResponse
from orchestrator.app.application.services.round_reconciliation_service import RoundReconciliationService
from orchestrator.app.domain.entities import Round

router = APIRouter(prefix="/rounds", tags=["rounds"])


def _to_response(round_record: Round) -> RoundResponse:
    return RoundResponse(
        round_id=round_record.round_id,
        job_id=round_record.job_id,
        protocol_name=round_record.protocol_name,
        round_index=round_record.round_index,
        status=round_record.status.value,
        base_model_artifact_uri=round_record.base_model_artifact_uri,
        aggregated_model_artifact_uri=round_record.aggregated_model_artifact_uri,
        aggregated_model_artifact_hash=round_record.aggregated_model_artifact_hash,
        evaluation_report_id=round_record.evaluation_report_id,
        failure_reason=round_record.failure_reason,
        created_at=round_record.created_at,
        updated_at=round_record.updated_at,
    )


@router.get("/{round_id}", response_model=RoundResponse)
def get_round(
    round_id: str,
    service: Annotated[RoundReconciliationService, Depends(get_round_reconciliation_service)],
) -> RoundResponse:
    round_record = service.get(round_id)
    if round_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="round not found")
    return _to_response(round_record)
