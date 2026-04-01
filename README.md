# distributed_training_marketplace

`distributed_training_marketplace` is an MVP repository for a distributed training marketplace with a strict on-chain/off-chain boundary.

## Current repository state
- Stage 1 is complete: generic on-chain trust and settlement layer in `contracts/`.
- Stage 2 is complete: orchestrator core with persistence, lifecycle handling, blockchain sync, node registry, and DB-backed API.
- Stage 3 is intentionally not started: no real training, datasets, aggregation, or evaluator execution yet.

## Architecture boundary
The blockchain layer is limited to trust and settlement concerns. Training, aggregation, evaluation, artifact storage, and node coordination remain off-chain.

## Key directories
- `contracts/`: canonical Foundry workspace for the trust layer.
- `docs/`: architecture, MVP, setup, and Codex guidance.
- `orchestrator/`: FastAPI orchestrator, persistence, sync, and lifecycle services.
- `trainer_agent/`, `evaluator_agent/`: placeholder service entrypoints for later stages.
- `shared/`: shared Python types used across off-chain services.
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
From the repository root:

```bash
export CHAIN_RPC_URL=http://127.0.0.1:8545
export CHAIN_ID=31337
export MARKETPLACE_CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
export DATABASE_URL=sqlite:///./data/orchestrator.db
make db-migrate
make orchestrator-run
```

Use PostgreSQL as the default target for non-trivial runs. SQLite remains available as a local fallback for development and tests.

## Manual local contract deploy
```bash
anvil
```

In another shell:

```bash
cd contracts
forge script script/DeployLocal.s.sol:DeployLocalScript \
  --rpc-url http://127.0.0.1:8545 \
  --broadcast \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

The canonical project documentation lives under `docs/`. Start with `docs/setup/development.md`, `docs/setup/local-demo.md`, and `docs/mvp/stage-2-plan.md`.
