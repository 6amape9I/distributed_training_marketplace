# Local Demo

All commands below are written from the repository root unless a section says otherwise.

## 1. Start local infrastructure
```bash
anvil
```

In a second shell:
```bash
export DATABASE_URL=sqlite:///./data/orchestrator.db
make db-migrate
make orchestrator-run
```

## 2. Start trainers
Shell 3:
```bash
export TRAINER_NODE_ID=trainer-1
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export TRAINER_PUBLIC_URL=http://127.0.0.1:8010
export LOCAL_WORKSPACE_PATH=./data/trainer-1
PYTHONPATH=. .venv/bin/uvicorn trainer_agent.app.main:create_app --factory --host 0.0.0.0 --port 8010
```

Shell 4:
```bash
export TRAINER_NODE_ID=trainer-2
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export TRAINER_PUBLIC_URL=http://127.0.0.1:8011
export LOCAL_WORKSPACE_PATH=./data/trainer-2
PYTHONPATH=. .venv/bin/uvicorn trainer_agent.app.main:create_app --factory --host 0.0.0.0 --port 8011
```

## 3. Seed a demo job and trainer tasks
Use the orchestrator internal endpoint after a job exists in the local DB:
```bash
curl -X POST http://127.0.0.1:8000/internal/tasks/seed-for-job/1
```

## 4. Observe execution
- trainers should register and stay online via heartbeat;
- each trainer should claim a different `local_fit` task;
- each completed task should upload a `task_result` and a `trainer_report` artifact;
- artifacts should appear under `ARTIFACT_ROOT`, while trainer-local working files appear under each trainer workspace.
