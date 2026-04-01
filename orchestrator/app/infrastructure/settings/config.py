from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(slots=True, frozen=True)
class Settings:
    host: str
    port: int
    chain_rpc_url: str
    database_url: str
    artifact_root: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        host=os.getenv("ORCHESTRATOR_HOST", "127.0.0.1"),
        port=int(os.getenv("ORCHESTRATOR_PORT", "8000")),
        chain_rpc_url=os.getenv("CHAIN_RPC_URL", "http://127.0.0.1:8545"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/orchestrator.db"),
        artifact_root=os.getenv("ARTIFACT_ROOT", "./artifacts"),
    )
