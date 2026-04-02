# distributed_training_marketplace

`distributed_training_marketplace` is an MVP repository for a distributed training marketplace with a strict on-chain/off-chain boundary.

## Current repository state
- Stage 1 is complete: generic on-chain trust and settlement layer in `contracts/`.
- Stage 2 is complete: orchestrator core with persistence, lifecycle handling, blockchain sync, node registry, and DB-backed API.
- Stage 3 is complete: trainer runtime, DB-backed training tasks, artifact upload/download, and real local `local_fit` execution.
- Stage 4 is now implemented: evaluator runtime, evaluation tasks/reports, metric computation, and lifecycle transitions into `ready_for_attestation` or `evaluation_failed`.
- Stage 5 is now implemented: round persistence, protocol plugin wiring, weighted aggregation, and plugin-driven end-to-end training plus evaluation.
- Stage 6 is now implemented: canonical Docker Compose demo stack, demo helper scripts, startup/readiness checks, and a reproducible local demo path.

## Architecture boundary
The blockchain layer remains limited to trust and settlement. Training, rounds, aggregation, evaluation, tasks, artifacts, and runtime coordination stay off-chain. Stage 5 still does not include on-chain attestation writes, final settlement execution, or Byzantine-robust aggregation.

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

## Canonical demo path
Stage 6 makes Docker Compose the only canonical local demo workflow. The demo publishes only:
- `8000` for orchestrator
- `8010` for `trainer-1`
- `8011` for `trainer-2`
- `8020` for `evaluator-1`

`anvil` and `postgres` stay internal to the Compose network. The canonical path does not require host-side `forge`, `cast`, or an externally exposed `8545` / `5432`.

Run:

```bash
make demo-up
make demo-init
make demo-start-flow
make demo-status
```

Expected final state after `make demo-start-flow`:
- job `1` reaches `ready_for_attestation` or `evaluation_failed`
- one round exists for the job
- two trainer tasks are completed
- one evaluation task is completed

One-command verification path from a fresh state:

```bash
make demo-smoke
```

## Low-level local runs
The manual single-process commands below remain available for debugging, but they are no longer the canonical demo path.

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
- `orchestrator/app/tests/test_protocol_round_flow.py` proves the Stage 5 path: protocol run -> trainer tasks -> aggregation -> evaluator task -> final lifecycle state.
- `make demo-smoke` is the Stage 6 operational path for the Compose demo stand.
- The live Stage 6 path has been verified with `make demo-clean && make demo-up && make demo-init && make demo-start-flow && make demo-status`.
- `docs/` is the canonical documentation tree.

Start with `docs/setup/local-demo.md`, `docs/setup/development.md`, and `docs/mvp/stage-6-plan.md`.
