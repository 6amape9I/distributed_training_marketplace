from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class StatusResponse(BaseModel):
    status: str
    database: dict[str, object]
    blockchain: dict[str, object]
    configured_chain_id: int
    contract_address: str
    last_processed_block: int | None = None


class ReconcileResponse(BaseModel):
    changed_jobs: int
