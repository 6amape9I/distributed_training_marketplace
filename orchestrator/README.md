# Orchestrator Core

Stage 2 turns the orchestrator into a real off-chain control plane.

## Responsibilities
- mirror contract events into persistent storage;
- maintain explicit off-chain job lifecycle state;
- expose DB-backed API endpoints for jobs, nodes, and status;
- support node registration and heartbeat flows;
- prepare funded jobs for future scheduling without dispatching real training work.

## Guardrails
- Do not change the Stage 1 contract model unless a real Stage 2 blocker is proven first.
- Do not pull Stage 3 into this service: no real training, datasets, aggregation, evaluator logic, or artifact execution flows.

## Environment variables
Required:
- `CHAIN_RPC_URL`
- `CHAIN_ID`
- `MARKETPLACE_CONTRACT_ADDRESS`
- `DATABASE_URL`

Optional:
- `ORCHESTRATOR_HOST`
- `ORCHESTRATOR_PORT`
- `ARTIFACT_ROOT`
- `SYNC_START_BLOCK`
- `SYNC_BATCH_SIZE`
- `NODE_STALE_AFTER_SECONDS`

## Local commands
```bash
PYTHONPATH=. .venv/bin/alembic -c orchestrator/alembic.ini upgrade head
PYTHONPATH=. .venv/bin/uvicorn orchestrator.app.api.main:create_app --factory --host 0.0.0.0 --port 8000
PYTHONPATH=. .venv/bin/pytest orchestrator/app/tests
```

## API surface
- `GET /health`
- `GET /status`
- `GET /jobs`
- `GET /jobs/{job_id}`
- `POST /jobs/sync`
- `GET /nodes`
- `GET /nodes/{node_id}`
- `POST /nodes/register`
- `POST /nodes/heartbeat`
- `POST /internal/sync/run-once`
- `POST /internal/lifecycle/reconcile`
