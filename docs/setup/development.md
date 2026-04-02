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

## Canonical public workflow
Stage 7 adds the first public trust-layer path and fixes one public target:
- `Base Sepolia`
- `chain_id=84532`

Public helper commands:

```bash
make public-check-env
make public-deploy
make public-create-job
make public-fund-job
make public-sync-job
make public-start-flow
make public-submit-attestation
make public-finalize-job
make public-withdraw
make public-status
```

Public env examples:
- `infra/env/public-demo.env.example`
- `infra/env/orchestrator.public.env.example`

Public runtime assumptions:
- orchestrator, `trainer-1`, `trainer-2`, and `evaluator-1` run locally;
- chain state is external on Base Sepolia;
- on-chain writes stay explicit in helper scripts, not hidden inside runtime side effects.

## Real dataset experiment workflow
The repository now includes one experiment-only path for the real WDBC dataset:

```bash
make experiment-prepare-data
make experiment-run-distributed
make experiment-run-baseline
make experiment-report
```

Use a fresh Stage 6 stand before `make experiment-run-distributed`:

```bash
make demo-clean
make demo-up
make demo-init
```

This experiment path:
- keeps `fedavg_like_v1` unchanged for the canonical Stage 6 demo;
- uses `fedavg_like_wdbc_v1` only for the WDBC experiment;
- writes processed manifests under `data/processed/wdbc/`;
- writes summaries and plots under `artifacts/experiments/real-training/`.

## Notes
- Stage 5 adds explicit `round` persistence and a plugin-driven execution path via `fedavg_like_v1`.
- The canonical off-chain flow is now `protocol run -> trainer tasks -> aggregation -> evaluation -> lifecycle reconcile`.
- Legacy manual routes `/internal/tasks/seed-for-job/{job_id}` and `/internal/evaluations/seed-for-job/{job_id}` remain only for earlier-stage smoke paths.
- Stage 6 adds the canonical Compose demo stand under `infra/compose/compose.demo.yml` and `infra/scripts/demo-*.sh`.
- `make demo-init` writes demo runtime state to `tmp/demo-state/current-run.env` for later steps.
- Stage 7 adds the canonical Base Sepolia helper surface under `infra/scripts/public-*.sh`.
- `make public-deploy` and follow-up commands write public runtime state to `tmp/public-state/current-run.env`.
- `make public-status` combines orchestrator API state, direct on-chain job reads, tx hashes, and balance checks.
- The WDBC experiment runbook lives in `docs/setup/real-training-experiment.md`.
- Job lifecycle now extends through `evaluating`, `ready_for_attestation`, and `evaluation_failed`.
- Contract ABI remains unchanged in Stage 7; public integration wraps the existing job/attestation/finalization/withdraw flow.
- The canonical Codex/project guidance lives in `docs/codex/`.
