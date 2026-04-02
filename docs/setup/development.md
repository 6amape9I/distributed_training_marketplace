# Development Setup

All commands below are written from the repository root unless a section says otherwise.

## Prerequisites
- Ubuntu-compatible shell environment
- Python 3.12
- Foundry (`forge`, `anvil`, `cast`)
- PostgreSQL for the default orchestrator setup

## Bootstrap
```bash
make check-env
make bootstrap-dev
```

## Contract workflow
```bash
make contracts-build
make contracts-test
make contracts-fmt
```

## Orchestrator DB migration
```bash
export DATABASE_URL=postgresql+psycopg://dtm:dtm@localhost:5432/dtm_orchestrator
make db-migrate
```

SQLite fallback for local-only work:
```bash
export DATABASE_URL=sqlite:///./data/orchestrator.db
make db-migrate
```

## Run the orchestrator
```bash
export CHAIN_RPC_URL=http://127.0.0.1:8545
export CHAIN_ID=31337
export MARKETPLACE_CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
make orchestrator-run
```

## Run trainers
```bash
export TRAINER_NODE_ID=trainer-1
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export TRAINER_PUBLIC_URL=http://127.0.0.1:8010
export LOCAL_WORKSPACE_PATH=./data/trainer-1
PYTHONPATH=. .venv/bin/uvicorn trainer_agent.app.main:create_app --factory --host 0.0.0.0 --port 8010
```

Start additional trainers with different `TRAINER_NODE_ID`, `TRAINER_PUBLIC_URL`, and `LOCAL_WORKSPACE_PATH` values.

## Run evaluators
```bash
export EVALUATOR_NODE_ID=evaluator-1
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export EVALUATOR_PUBLIC_URL=http://127.0.0.1:8020
export LOCAL_WORKSPACE_PATH=./data/evaluator-1
PYTHONPATH=. .venv/bin/uvicorn evaluator_agent.app.main:create_app --factory --host 0.0.0.0 --port 8020
```

## Python test suite
```bash
make python-test
```

## Canonical demo workflow
Stage 6 standardizes the demo stand around Docker Compose and helper scripts:

```bash
make demo-up
make demo-init
make demo-start-flow
make demo-status
```

Use `make demo-clean` to reset the stand to a fresh deterministic state.

Demo networking details:
- only `8000`, `8010`, `8011`, and `8020` are published to the host;
- `anvil` and `postgres` are internal-only services in `infra/compose/compose.demo.yml`;
- the canonical demo path does not depend on host `forge`, `cast`, or host access to `127.0.0.1:8545`.

## Notes
- Stage 5 adds explicit `round` persistence and a plugin-driven execution path via `fedavg_like_v1`.
- The canonical off-chain flow is now `protocol run -> trainer tasks -> aggregation -> evaluation -> lifecycle reconcile`.
- Legacy manual routes `/internal/tasks/seed-for-job/{job_id}` and `/internal/evaluations/seed-for-job/{job_id}` remain only for earlier-stage smoke paths.
- Stage 6 adds the canonical Compose demo stand under `infra/compose/compose.demo.yml` and `infra/scripts/demo-*.sh`.
- `make demo-init` writes demo runtime state to `tmp/demo-state/current-run.env` for later steps.
- Job lifecycle now extends through `evaluating`, `ready_for_attestation`, and `evaluation_failed`.
- Contract ABI and on-chain flows remain unchanged in Stage 6.
- The canonical Codex/project guidance lives in `docs/codex/`.
