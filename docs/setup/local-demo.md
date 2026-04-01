# Local Demo

All commands below are written from the repository root unless a section says otherwise.
If your shell is currently in `docs/setup`, run `cd ../..` first.

## 1. Start local infrastructure
Shell 1:
```bash
anvil
```

Shell 2:
```bash
cd contracts
forge script script/DeployLocal.s.sol:DeployLocalScript \
  --rpc-url http://127.0.0.1:8545 \
  --broadcast \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

Shell 3:
```bash
export CHAIN_RPC_URL=http://127.0.0.1:8545
export CHAIN_ID=31337
export MARKETPLACE_CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
export DATABASE_URL=sqlite:///./data/orchestrator.db
make db-migrate
make orchestrator-run
```

## 2. Start two trainers
Shell 4:
```bash
export TRAINER_NODE_ID=trainer-1
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export TRAINER_PUBLIC_URL=http://127.0.0.1:8010
export LOCAL_WORKSPACE_PATH=./data/trainer-1
PYTHONPATH=. .venv/bin/uvicorn trainer_agent.app.main:create_app --factory --host 0.0.0.0 --port 8010
```

Shell 5:
```bash
export TRAINER_NODE_ID=trainer-2
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export TRAINER_PUBLIC_URL=http://127.0.0.1:8011
export LOCAL_WORKSPACE_PATH=./data/trainer-2
PYTHONPATH=. .venv/bin/uvicorn trainer_agent.app.main:create_app --factory --host 0.0.0.0 --port 8011
```

## 3. Start one evaluator
Shell 6:
```bash
export EVALUATOR_NODE_ID=evaluator-1
export ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000
export EVALUATOR_PUBLIC_URL=http://127.0.0.1:8020
export LOCAL_WORKSPACE_PATH=./data/evaluator-1
PYTHONPATH=. .venv/bin/uvicorn evaluator_agent.app.main:create_app --factory --host 0.0.0.0 --port 8020
```

## 4. Create and fund one on-chain job
Shell 7:
```bash
cast send 0x5FbDB2315678afecb367f032d93F642f64180aa3 \
  "createJob(address,address,uint256,bytes32)" \
  0x70997970C51812dc3A010C7d01b50e0d17dc79C8 \
  0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC \
  1000000000000000000 \
  0x1111111111111111111111111111111111111111111111111111111111111111 \
  --rpc-url http://127.0.0.1:8545 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

cast send 0x5FbDB2315678afecb367f032d93F642f64180aa3 \
  "fundJob(uint256)" 1 \
  --value 1000000000000000000 \
  --rpc-url http://127.0.0.1:8545 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

## 5. Sync and move the job into `scheduling`
```bash
curl -X POST http://127.0.0.1:8000/jobs/sync
curl -X POST http://127.0.0.1:8000/internal/lifecycle/reconcile
curl -X POST http://127.0.0.1:8000/internal/lifecycle/reconcile
curl http://127.0.0.1:8000/jobs/1
```

At that point the job should report `offchain_status = "scheduling"`.

## 6. Start the protocol-driven round
```bash
curl -X POST http://127.0.0.1:8000/internal/protocol-runs/start-for-job/1
curl http://127.0.0.1:8000/jobs/1/rounds
```

The response contains the `round_id`. Trainers will claim `local_fit` tasks automatically.

## 7. Reconcile aggregation and evaluation
After both trainers complete their tasks:
```bash
curl -X POST http://127.0.0.1:8000/internal/rounds/<round_id>/reconcile
```

This creates the aggregated model artifact and seeds one evaluator task for that round. After the evaluator completes:
```bash
curl -X POST http://127.0.0.1:8000/internal/rounds/<round_id>/reconcile
curl http://127.0.0.1:8000/rounds/<round_id>
curl http://127.0.0.1:8000/jobs/1
```

## 8. Observe execution
- trainers should register, heartbeat, and claim distinct `local_fit` tasks for the same `round_id`;
- completed trainer tasks should upload `task_result` and `trainer_report` artifacts;
- the round reconciliation step should create a real aggregated model artifact;
- the evaluator should claim the aggregated-model evaluation task and upload an `evaluation_report` artifact;
- the job should transition to `ready_for_attestation` when the aggregated model passes the acceptance threshold, otherwise to `evaluation_failed`.

## 9. Automated smoke checks
```bash
PYTHONPATH=. .venv/bin/pytest -q trainer_agent/app/tests/test_multi_runtime_smoke.py
PYTHONPATH=. .venv/bin/pytest -q orchestrator/app/tests/test_protocol_round_flow.py
PYTHONPATH=. .venv/bin/pytest -q orchestrator/app/tests/test_evaluator_task_flow.py evaluator_agent/app/tests
```

These tests cover the Stage 3 multi-trainer caveat, the Stage 4 evaluator flow, and the Stage 5 plugin-driven round flow without requiring the full live demo each time.
