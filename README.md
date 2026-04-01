# distributed_training_marketplace

`distributed_training_marketplace` is an MVP repository for a distributed training marketplace with a strict on-chain/off-chain boundary.

## Current repository state
- Stage 1 is complete: generic on-chain trust and settlement layer in `contracts/`.
- Stage 2 is complete: orchestrator core with persistence, lifecycle handling, blockchain sync, node registry, and DB-backed API.
- Stage 3 is complete: trainer runtime, DB-backed training tasks, artifact upload/download, and real local `local_fit` execution.
- Stage 4 is now implemented: evaluator runtime, evaluation tasks/reports, metric computation, and lifecycle transitions into `ready_for_attestation` or `evaluation_failed`.

## Architecture boundary
The blockchain layer remains limited to trust and settlement. Training, evaluation, tasks, artifacts, and runtime coordination stay off-chain. Stage 4 still does not include on-chain attestation writes, final settlement execution, or a production aggregation framework.

## Key directories
- `contracts/`: canonical Foundry workspace for the trust layer.
- `docs/`: architecture, MVP, setup, and Codex guidance.
- `orchestrator/`: FastAPI orchestrator, persistence, sync, node registry, trainer/evaluator task APIs, and artifact services.
- `trainer_agent/`: trainer worker service with registration, heartbeat, task claiming, and local training execution.
- `evaluator_agent/`: evaluator worker service with registration, heartbeat, evaluation task claiming, and metric computation.
- `shared/`: shared Python schemas and hashing helpers.
- `infra/`: Docker Compose, env examples, Dockerfiles, and helper scripts.

## Quick start
```bash
make check-env
make bootstrap-dev
make contracts-test
make db-migrate
make python-test
```

## Run the orchestrator locally
```bash
export CHAIN_RPC_URL=http://127.0.0.1:8545
export CHAIN_ID=31337
export MARKETPLACE_CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
export DATABASE_URL=sqlite:///./data/orchestrator.db
make db-migrate
make orchestrator-run
```

## Run a trainer locally
```bash
export TRAINER_NODE_ID=trainer-1
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export TRAINER_PUBLIC_URL=http://127.0.0.1:8010
export LOCAL_WORKSPACE_PATH=./data/trainer-1
PYTHONPATH=. .venv/bin/uvicorn trainer_agent.app.main:create_app --factory --host 0.0.0.0 --port 8010
```

## Run an evaluator locally
```bash
export EVALUATOR_NODE_ID=evaluator-1
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export EVALUATOR_PUBLIC_URL=http://127.0.0.1:8020
export LOCAL_WORKSPACE_PATH=./data/evaluator-1
PYTHONPATH=. .venv/bin/uvicorn evaluator_agent.app.main:create_app --factory --host 0.0.0.0 --port 8020
```

## Verification
- `make python-test` now covers orchestrator, trainer, and evaluator suites.
- `trainer_agent/app/tests/test_multi_runtime_smoke.py` closes the Stage 3 multi-trainer caveat with an explicit two-runtime smoke test.
- `docs/` is the canonical documentation tree.

Start with `docs/setup/development.md`, `docs/setup/local-demo.md`, and `docs/mvp/stage-4-plan.md`.
