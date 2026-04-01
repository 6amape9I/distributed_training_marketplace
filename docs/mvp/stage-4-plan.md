# Stage 4 Plan Tracker

## Status
Stage 4 is implemented.

## Delivered scope
- real evaluator runtime with settings, registration, heartbeat, polling, and status endpoints;
- persistent evaluation task and evaluation report models plus Alembic migration;
- evaluator task APIs:
  - `POST /evaluator/tasks/claim`
  - `POST /evaluator/tasks/{task_id}/start`
  - `POST /evaluator/tasks/{task_id}/complete`
  - `POST /evaluator/tasks/{task_id}/fail`
  - `GET /evaluator/tasks/{task_id}`
  - `POST /internal/evaluations/seed-for-job/{job_id}`
- evaluation artifact flow with `evaluation_report` and `evaluation_input_manifest` kinds;
- metric computation against trainer-produced model artifacts;
- lifecycle integration into `evaluating`, `ready_for_attestation`, and `evaluation_failed`.

## Guardrails preserved
- Stage 1 contract model unchanged.
- No on-chain attestation writes or settlement execution added.
- Trainer/task/artifact architecture from Stage 3 reused rather than redesigned.
- Evaluation remains off-chain and intentionally minimal.

## Acceptance rule
Stage 4 uses a fixed MVP acceptance threshold:
- `accuracy >= 0.75` => accepted
- otherwise => rejected and the job moves to `evaluation_failed`

## Main implementation points
### Evaluator agent
- `evaluator_agent/` now mirrors the trainer runtime pattern with a dedicated orchestrator client and evaluation executor.
- Evaluators register as `role=evaluator`, heartbeat, claim work, download artifacts, compute metrics, upload reports, and complete tasks.

### Orchestrator
- `orchestrator/` now persists `evaluation_tasks` and `evaluation_reports`.
- Evaluation seeding creates one evaluation task per completed training task.
- Completion reconciliation updates job lifecycle based on all evaluation outcomes.

### Artifact flow
- Evaluation reports are stored off-chain through the same artifact service used in Stage 3.
- Orchestrator stores only metadata and references.

## Verification
- `make python-test`
- `forge test`
- focused smoke paths:
  - `trainer_agent/app/tests/test_multi_runtime_smoke.py`
  - `orchestrator/app/tests/test_evaluator_task_flow.py`
  - `evaluator_agent/app/tests/test_evaluation_executor.py`
  - `evaluator_agent/app/tests/test_evaluator_runtime.py`

## Out of scope
- on-chain attestation submission;
- settlement execution from evaluation output;
- production aggregation framework;
- trustless verification, slashing, or reputation logic;
- UI or broader orchestration redesign.
