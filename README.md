# distributed_training_marketplace

`distributed_training_marketplace` is an MVP repository for a distributed training marketplace with a strict on-chain/off-chain boundary.

## Stage 1 outcome
- generic smart-contract trust layer for job registration, escrow, attestations, finalization, payouts, and refunds;
- baseline repository structure and architecture documentation;
- Python scaffolding for the orchestrator and agent services;
- local developer scripts for contract-first smoke testing.

## Architecture boundary
The blockchain layer is limited to trust and settlement concerns. Training, aggregation, evaluation, artifact storage, and node coordination remain off-chain.

## Key directories
- `contracts/`: canonical Foundry workspace for the trust layer.
- `docs/`: architecture, MVP, setup, and Codex guidance.
- `orchestrator/`: FastAPI scaffold and protocol extension points.
- `trainer_agent/`, `evaluator_agent/`: placeholder service entrypoints.
- `shared/`: shared Python types used across off-chain services.
- `infra/`: Docker Compose, env examples, Dockerfiles, and local helper scripts.

## Quick start
```bash
make check-env
make contracts-build
make contracts-test
make python-test
```

## Manual local deploy
Run these commands from the repository root:

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

The canonical project documentation lives under `docs/`. Start with `docs/setup/development.md` and `docs/setup/local-demo.md`.
