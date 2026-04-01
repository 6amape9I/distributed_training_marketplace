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

## 2. Start two trainers
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

## 3. Start one evaluator
Shell 5:
```bash
export EVALUATOR_NODE_ID=evaluator-1
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export EVALUATOR_PUBLIC_URL=http://127.0.0.1:8020
export LOCAL_WORKSPACE_PATH=./data/evaluator-1
PYTHONPATH=. .venv/bin/uvicorn evaluator_agent.app.main:create_app --factory --host 0.0.0.0 --port 8020
```

## 4. Seed a demo job and trainer tasks
After a job exists in the local DB:
```bash
curl -X POST http://127.0.0.1:8000/internal/tasks/seed-for-job/1
```

## 5. Seed evaluation tasks after trainers finish
Once trainer tasks are completed:
```bash
curl -X POST http://127.0.0.1:8000/internal/evaluations/seed-for-job/1
```

## 6. Observe execution
- trainers should register, heartbeat, and claim distinct `local_fit` tasks;
- completed trainer tasks should upload `task_result` and `trainer_report` artifacts;
- evaluator should register, heartbeat, claim evaluation tasks, and upload `evaluation_report` artifacts;
- the job should transition to `ready_for_attestation` when all evaluation reports pass the acceptance threshold, otherwise to `evaluation_failed`.

## 7. Automated smoke checks
```bash
PYTHONPATH=. .venv/bin/pytest -q trainer_agent/app/tests/test_multi_runtime_smoke.py
PYTHONPATH=. .venv/bin/pytest -q orchestrator/app/tests/test_evaluator_task_flow.py evaluator_agent/app/tests
```

These tests cover the Stage 3 multi-trainer caveat and the Stage 4 evaluator flow without requiring the full live demo each time.
