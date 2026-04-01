from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os

from web3 import Web3


class SettingsError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class Settings:
    host: str
    port: int
    chain_rpc_url: str
    chain_id: int
    marketplace_contract_address: str
    database_url: str
    artifact_root: str
    sync_start_block: int
    sync_batch_size: int
    node_stale_after_seconds: int


_REQUIRED_ENV = ("CHAIN_RPC_URL", "CHAIN_ID", "MARKETPLACE_CONTRACT_ADDRESS", "DATABASE_URL")


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise SettingsError(f"Missing required environment variable: {name}")
    return value


def _read_int(name: str, default: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        if default is None:
            raise SettingsError(f"Missing required integer environment variable: {name}")
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise SettingsError(f"Invalid integer value for {name}: {raw}") from exc


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    for required in _REQUIRED_ENV:
        _require_env(required)

    contract_address = _require_env("MARKETPLACE_CONTRACT_ADDRESS")
    if not Web3.is_address(contract_address):
        raise SettingsError("MARKETPLACE_CONTRACT_ADDRESS is not a valid EVM address")

    return Settings(
        host=os.getenv("ORCHESTRATOR_HOST", "127.0.0.1"),
        port=_read_int("ORCHESTRATOR_PORT", 8000),
        chain_rpc_url=_require_env("CHAIN_RPC_URL"),
        chain_id=_read_int("CHAIN_ID"),
        marketplace_contract_address=Web3.to_checksum_address(contract_address),
        database_url=_require_env("DATABASE_URL"),
        artifact_root=os.getenv("ARTIFACT_ROOT", "./artifacts"),
        sync_start_block=_read_int("SYNC_START_BLOCK", 0),
        sync_batch_size=_read_int("SYNC_BATCH_SIZE", 500),
        node_stale_after_seconds=_read_int("NODE_STALE_AFTER_SECONDS", 120),
    )
