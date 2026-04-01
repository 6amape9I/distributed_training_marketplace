from typing import Annotated

from fastapi import APIRouter, Depends

from orchestrator.app.api.deps import get_app_settings
from orchestrator.app.infrastructure.settings import Settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: Annotated[Settings, Depends(get_app_settings)]) -> dict[str, str | int]:
    return {"status": "ok", "rpc_url": settings.chain_rpc_url, "port": settings.port}
