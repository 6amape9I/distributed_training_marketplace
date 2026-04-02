# Public Demo

All commands below are written from the repository root. Stage 7 defines one canonical public target:
- `Base Sepolia`
- `chain_id=84532`

The public demo keeps orchestrator and workers local, but moves the trust layer to the public chain.

## Prerequisites
- `make bootstrap-dev`
- a working Base Sepolia RPC URL
- funded testnet accounts for:
  - deployer
  - requester
  - provider
  - attestor
- one local orchestrator process
- two local trainer processes: `trainer-1`, `trainer-2`
- one local evaluator process: `evaluator-1`

Canonical env examples:
- `infra/env/public-demo.env.example`
- `infra/env/orchestrator.public.env.example`

## 1. Validate public env
```bash
source infra/env/public-demo.env.example
make public-check-env
```

This validates:
- RPC reachability
- chain id match
- required private keys
- derived role addresses

Keep this env loaded for the rest of the public run, or source it again before each `make public-*` command.

## 2. Deploy the public contract
```bash
make public-deploy
source tmp/public-state/current-run.env
```

This writes the deployed contract address and deployment tx hash into the public state file.

## 3. Start local off-chain services
Run the orchestrator against Base Sepolia using the deployed contract address:

```bash
export $(grep -v '^#' infra/env/orchestrator.public.env.example | xargs)
export CHAIN_RPC_URL="$PUBLIC_RPC_URL"
export MARKETPLACE_CONTRACT_ADDRESS="$CONTRACT_ADDRESS"
make db-migrate
make orchestrator-run
```

Run workers in separate shells:

```bash
export TRAINER_NODE_ID=trainer-1
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export TRAINER_PUBLIC_URL=http://127.0.0.1:8010
export LOCAL_WORKSPACE_PATH=./data/trainer-1
PYTHONPATH=. .venv/bin/uvicorn trainer_agent.app.main:create_app --factory --host 0.0.0.0 --port 8010
```

```bash
export TRAINER_NODE_ID=trainer-2
export TRAINER_PUBLIC_URL=http://127.0.0.1:8011
export LOCAL_WORKSPACE_PATH=./data/trainer-2
PYTHONPATH=. .venv/bin/uvicorn trainer_agent.app.main:create_app --factory --host 0.0.0.0 --port 8011
```

```bash
export EVALUATOR_NODE_ID=evaluator-1
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export EVALUATOR_PUBLIC_URL=http://127.0.0.1:8020
export LOCAL_WORKSPACE_PATH=./data/evaluator-1
PYTHONPATH=. .venv/bin/uvicorn evaluator_agent.app.main:create_app --factory --host 0.0.0.0 --port 8020
```

## 4. Create, fund, sync
```bash
make public-create-job
make public-fund-job
make public-sync-job
```

This path:
- reuses the Stage 7 deployment from `make public-deploy`
- stores deployment metadata in `tmp/public-state/deployments/base-sepolia.json`
- creates one public job
- funds the escrow on-chain
- imports that job into the orchestrator
- waits for `trainer-1`, `trainer-2`, and `evaluator-1`
- moves the job into `scheduling`

## 5. Run the off-chain flow
```bash
make public-start-flow
```

Expected final off-chain state:
- `ready_for_attestation`, or
- `evaluation_failed`

The canonical public success path continues only from `ready_for_attestation`.

## 6. Submit attestation and finalize
```bash
make public-submit-attestation
make public-finalize-job
```

Attestation details:
- payload is built deterministically from the synced job, round, and completed evaluation task
- payload and hash are written under `tmp/public-state/`
- the attestor key is the only key used for `submitAttestation`

Settlement details:
- Stage 7 success policy is fixed at `90% provider payout / 10% requester refund`
- settlement payload and hash are written under `tmp/public-state/`
- `finalizeJob` is sent with the attestor key

## 7. Withdraw and verify
```bash
make public-withdraw
make public-status
```

`make public-status` prints:
- network, chain id, RPC URL
- current public run state file
- orchestrator `/health` and `/status`
- synced job / rounds / training tasks / evaluation tasks
- direct on-chain job state
- tx summaries for deploy, create, fund, attestation, finalization, withdrawals
- requester and provider balances

## Notes
- Stage 7 keeps all training, aggregation, and evaluation off-chain.
- The Stage 1 contract ABI is unchanged.
- The canonical success settlement split is deterministic and inspectable.
- Public runtime state lives in `tmp/public-state/current-run.env`.
- If a run ends in `evaluation_failed`, the canonical Stage 7 runbook stops before attestation/finalization.
