# Stage 2 Plan Tracker

## Stage objective

Implement the orchestrator core for the distributed training marketplace.

## Codex guardrails for Stage 2
- Do not change the Stage 1 contract model unless a real Stage 2 blocker is proven first.
- If a contract change is proposed, the agent must first show why Stage 2 cannot be completed against the current ABI/events.
- Do not pull Stage 3 into Stage 2.
- As soon as implementation starts adding real training, datasets, aggregation, or evaluator execution, it has left the stage boundary.

## Stage 2 implementation status
- Application bootstrap hardening: complete
- Persistent storage and Alembic bootstrap: complete
- Off-chain lifecycle service: complete
- Blockchain sync and event mapping: complete
- Node registry and liveness flow: complete
- Real REST API: complete
- Orchestration service skeleton: complete
- Test expansion: complete
- Documentation update: complete

## Delivered behavior
Stage 2 now provides:
- a factory-based FastAPI orchestrator application;
- centralized settings and dependency wiring;
- SQLAlchemy persistence for jobs, nodes, chain sync state, and processed job events;
- Alembic migration bootstrap under `orchestrator/alembic/`;
- explicit on-chain/off-chain lifecycle separation;
- deterministic polling-based blockchain sync with idempotent event handling;
- node registration and heartbeat endpoints;
- internal sync and lifecycle reconcile endpoints;
- pytest coverage for lifecycle logic, node registration, event sync, and DB-backed route behavior.

## Explicitly deferred to Stage 3
- real training execution
- datasets
- round execution
- aggregation logic
- evaluator logic
- artifact movement and checkpoint workflows
- task dispatch from orchestrator to trainer/evaluator nodes

## Operational notes
- PostgreSQL is the default target for orchestrator runtime.
- SQLite remains available as a local fallback for tests and lightweight development.
- The Stage 1 contract ABI and event model remain unchanged in Stage 2.
