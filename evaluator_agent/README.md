# Evaluator Agent

Stage 4 turns `evaluator_agent/` into a real worker service.

## Responsibilities
- register as an evaluator node in the orchestrator;
- maintain heartbeat and self-status;
- claim evaluation tasks;
- download trainer result artifacts and evaluation manifests;
- compute metrics and acceptance decisions;
- upload evaluation report artifacts and complete or fail tasks.

## Required environment variables
- `SERVICE_NAME`
- `EVALUATOR_NODE_ID`
- `ORCHESTRATOR_BASE_URL`
- `EVALUATOR_BIND_HOST`
- `EVALUATOR_BIND_PORT`
- `EVALUATOR_PUBLIC_URL`
- `HEARTBEAT_INTERVAL_SECONDS`
- `TASK_POLL_INTERVAL_SECONDS`
- `LOCAL_WORKSPACE_PATH`

Optional:
- `EVALUATOR_CAPABILITIES_JSON`
- `ENABLE_BACKGROUND_WORKERS`

## Local command
```bash
PYTHONPATH=. .venv/bin/uvicorn evaluator_agent.app.main:create_app --factory --host 0.0.0.0 --port 8020
```
