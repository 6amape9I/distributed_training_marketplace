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

## Python test suite
```bash
make python-test
```

## Notes
- Stage 3 includes real trainer execution and artifact movement.
- Stage 3 still does not include evaluator execution, productized aggregation, or settlement finalization from training results.
- The canonical Codex/project guidance lives in `docs/codex/`.
