from __future__ import annotations

import base64
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from orchestrator.app.api.deps import get_artifact_service, get_db_session
from orchestrator.app.application.dto import ArtifactContentResponse, ArtifactResponse, ArtifactUploadRequest
from orchestrator.app.application.services import ArtifactNotFoundError, ArtifactService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.post("/upload", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
def upload_artifact(
    payload: ArtifactUploadRequest,
    service: Annotated[ArtifactService, Depends(get_artifact_service)],
    session: Annotated[Session | None, Depends(get_db_session)] = None,
) -> ArtifactResponse:
    artifact = service.upload_base64(
        kind=payload.kind,
        name=payload.name,
        payload_base64=payload.payload_base64,
        mime_type=payload.mime_type,
        metadata=payload.metadata,
        job_id=payload.job_id,
        task_id=payload.task_id,
    )
    if session is not None:
        session.commit()
    return ArtifactResponse(
        artifact_id=artifact.artifact_id,
        kind=artifact.kind.value,
        uri=artifact.uri,
        content_hash=artifact.content_hash,
        content_size_bytes=artifact.content_size_bytes,
        mime_type=artifact.mime_type,
        metadata_json=artifact.metadata_json,
        job_id=artifact.job_id,
        task_id=artifact.task_id,
        created_at=artifact.created_at,
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(
    artifact_id: str,
    service: Annotated[ArtifactService, Depends(get_artifact_service)],
) -> ArtifactResponse:
    try:
        artifact = service.get(artifact_id)
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ArtifactResponse(
        artifact_id=artifact.artifact_id,
        kind=artifact.kind.value,
        uri=artifact.uri,
        content_hash=artifact.content_hash,
        content_size_bytes=artifact.content_size_bytes,
        mime_type=artifact.mime_type,
        metadata_json=artifact.metadata_json,
        job_id=artifact.job_id,
        task_id=artifact.task_id,
        created_at=artifact.created_at,
    )


@router.get("/{artifact_id}/content", response_model=ArtifactContentResponse)
def get_artifact_content(
    artifact_id: str,
    service: Annotated[ArtifactService, Depends(get_artifact_service)],
) -> ArtifactContentResponse:
    try:
        artifact = service.get(artifact_id)
        payload = service.read_content(artifact_id)
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ArtifactContentResponse(
        artifact_id=artifact.artifact_id,
        mime_type=artifact.mime_type,
        payload_base64=base64.b64encode(payload).decode("utf-8"),
    )
