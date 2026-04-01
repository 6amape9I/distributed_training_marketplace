# Orchestrator Core

Stage 3 extends the orchestrator into the first real off-chain execution control plane.

## Responsibilities
- mirror contract events into persistent storage;
- maintain explicit off-chain job lifecycle state;
- expose DB-backed API endpoints for jobs, nodes, trainer tasks, artifacts, and status;
- support node registration and heartbeat flows;
- seed and track trainer tasks;
- persist artifact metadata and serve artifact content.

## Guardrails
- Do not change the Stage 1 contract model unless a real blocker is proven first.
- Do not pull evaluator execution, productized aggregation, or settlement finalization into this service yet.

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
PYTHONPATH=. .venv/bin/pytest orchestrator/app/tests trainer_agent/app/tests
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
- `POST /trainer/tasks/claim`
- `POST /trainer/tasks/{task_id}/start`
- `POST /trainer/tasks/{task_id}/complete`
- `POST /trainer/tasks/{task_id}/fail`
- `GET /trainer/tasks/{task_id}`
- `POST /artifacts/upload`
- `GET /artifacts/{artifact_id}`
- `GET /artifacts/{artifact_id}/content`
- `POST /internal/tasks/seed-for-job/{job_id}`
