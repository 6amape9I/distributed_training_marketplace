from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


class TrainerSettingsError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class TrainerSettings:
    service_name: str
    trainer_node_id: str
    orchestrator_base_url: str
    trainer_bind_host: str
    trainer_bind_port: int
    trainer_public_url: str
    heartbeat_interval_seconds: int
    task_poll_interval_seconds: int
    local_workspace_path: str
    artifact_upload_mode: str
    trainer_capabilities_json: str | None
    enable_background_workers: bool



def _require(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value.strip() == "":
        raise TrainerSettingsError(f"Missing required environment variable: {name}")
    return value



def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise TrainerSettingsError(f"Invalid integer value for {name}: {raw}") from exc



def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> TrainerSettings:
    bind_host = _require("TRAINER_BIND_HOST", "0.0.0.0")
    bind_port = _read_int("TRAINER_BIND_PORT", 8010)
    return TrainerSettings(
        service_name=_require("SERVICE_NAME", "trainer-agent"),
        trainer_node_id=_require("TRAINER_NODE_ID"),
        orchestrator_base_url=_require("ORCHESTRATOR_BASE_URL"),
        trainer_bind_host=bind_host,
        trainer_bind_port=bind_port,
        trainer_public_url=_require("TRAINER_PUBLIC_URL", f"http://{bind_host}:{bind_port}"),
        heartbeat_interval_seconds=_read_int("HEARTBEAT_INTERVAL_SECONDS", 10),
        task_poll_interval_seconds=_read_int("TASK_POLL_INTERVAL_SECONDS", 2),
        local_workspace_path=_require("LOCAL_WORKSPACE_PATH", "./data/trainer-workspace"),
        artifact_upload_mode=_require("ARTIFACT_UPLOAD_MODE", "orchestrator_http"),
        trainer_capabilities_json=os.getenv("TRAINER_CAPABILITIES_JSON"),
        enable_background_workers=_read_bool("ENABLE_BACKGROUND_WORKERS", True),
    )
