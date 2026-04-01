# Development Setup

All commands below are written from the repository root unless a section says otherwise.

## Prerequisites
- Ubuntu-compatible shell environment
- Python 3.12
- Foundry (`forge`, `anvil`, `cast`)
- PostgreSQL for the default Stage 2 orchestrator setup

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
Default Stage 2 target:
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

## Python test suite
```bash
make python-test
```

## Notes
- Stage 2 does not include real training, datasets, aggregation, or evaluator execution.
- Stage 2 should not change the contract model unless a hard blocker is proven first.
- Root environment defaults live in `.env.example`, while service-specific examples live under `infra/env/`.
- The canonical Codex/project guidance lives in `docs/codex/`.
