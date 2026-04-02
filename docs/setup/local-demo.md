# Local Demo

All commands below are written from the repository root. Stage 6 makes `infra/compose/compose.demo.yml` the only canonical local demo stand.

## Prerequisites
- Docker with `docker compose`
- `curl`
- `python3`
- enough free ports for `8545`, `5432`, `8000`, `8010`, `8011`, `8020`

## 1. Start the stand
```bash
make demo-up
```

This brings up:
- `anvil`
- `postgres`
- `orchestrator`
- `trainer-1`
- `trainer-2`
- `evaluator-1`

It also runs DB migrations and waits for `/health` readiness.

## 2. Initialize the demo
```bash
make demo-init
```

This step:
- deploys `TrainingMarketplace` to the fresh local chain;
- creates and funds demo job `1` on-chain;
- syncs it into the orchestrator;
- waits for both trainers and the evaluator to register;
- advances the job into `scheduling`.

## 3. Run the protocol flow
```bash
make demo-start-flow
```

This step:
- starts the Stage 5 protocol run for job `1`;
- waits for both trainer tasks to finish;
- reconciles the round into aggregation and evaluation;
- waits for the evaluator task to finish;
- reconciles the final job state.

Expected final state:
- `ready_for_attestation`, or
- `evaluation_failed`

## 4. Inspect the result
```bash
make demo-status
make demo-logs
```

`make demo-status` prints:
- orchestrator `/health` and `/status`
- node registry state
- jobs
- rounds
- training tasks
- evaluation tasks
- trainer/evaluator worker `/status`

If you want a single validation path before a presentation:

```bash
make demo-smoke
```

## 5. Cleanup
Stop the stand but keep volumes:

```bash
make demo-down
```

Remove containers, volumes, and local demo state:

```bash
make demo-clean
```

## Notes
- The demo assumes a fresh chain and fresh Compose volumes.
- `make demo-init` will fail fast if the chain is not fresh enough to deploy to the expected deterministic local address.
- The older multi-shell manual flow is now a low-level fallback for debugging, not the recommended demo path.
