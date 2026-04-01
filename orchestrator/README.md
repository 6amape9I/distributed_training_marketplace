# Orchestrator Core

Stage 4 extends the orchestrator into the first real training-plus-evaluation control plane.

## Responsibilities
- mirror contract events into persistent storage;
- maintain explicit off-chain job lifecycle state;
- expose DB-backed API endpoints for jobs, nodes, trainer tasks, evaluator tasks, artifacts, and status;
- support node registration and heartbeat flows;
- seed and track trainer and evaluator tasks;
- persist artifact and evaluation report metadata;
- reconcile job state after training and evaluation completion.

## Guardrails
- Do not change the Stage 1 contract model unless a real blocker is proven first.
- Do not pull on-chain attestation writes or settlement execution into this service.

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
PYTHONPATH=. .venv/bin/pytest orchestrator/app/tests trainer_agent/app/tests evaluator_agent/app/tests
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
- `POST /evaluator/tasks/claim`
- `POST /evaluator/tasks/{task_id}/start`
- `POST /evaluator/tasks/{task_id}/complete`
- `POST /evaluator/tasks/{task_id}/fail`
- `GET /evaluator/tasks/{task_id}`
- `POST /artifacts/upload`
- `GET /artifacts/{artifact_id}`
- `GET /artifacts/{artifact_id}/content`
- `POST /internal/tasks/seed-for-job/{job_id}`
- `POST /internal/evaluations/seed-for-job/{job_id}`
