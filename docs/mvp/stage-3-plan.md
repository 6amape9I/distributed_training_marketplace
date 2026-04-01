# Stage 3 Plan Tracker

## Stage objective

Implement the first real trainer-agent execution flow for the distributed training marketplace.

## Codex guardrails for Stage 3
- Do not change the Stage 1 contract model.
- Do not collapse the architecture into a FedAvg-specific implementation.
- Do not move evaluation logic into this stage except for trainer-local training reports.
- Do not bypass the orchestrator; trainer agents must work through orchestrator-controlled task APIs and artifact handling.
- Keep artifact movement generic enough to support later protocol changes.

## Stage 3 implementation status
- Trainer application bootstrap: complete
- Trainer registration and heartbeat: complete
- Training task model: complete
- Orchestrator task APIs: complete
- Artifact upload flow: complete
- Local training execution: complete
- Demo dataset and shard flow: complete
- Multi-trainer runtime demo scaffolding: complete
- Tests: complete
- Documentation: complete

## Delivered behavior
Stage 3 now provides:
- a real trainer service with registration, heartbeat, task claiming, and self-status endpoints;
- persistent orchestrator-side `training_tasks` and `artifacts` tables;
- DB-backed claim/start/complete/fail trainer task APIs;
- local filesystem artifact storage with hash persistence and content download;
- a real `local_fit` executor that trains a small logistic-style model on deterministic demo partitions;
- orchestrator-side task seeding for multiple online trainer nodes;
- pytest coverage for task flow, local execution, and trainer runtime behavior.

## Explicitly deferred to Stage 4+
- evaluator execution
- global aggregation as a product flow
- blockchain writes from training outputs
- contribution scoring, trustless validation, and Byzantine defenses
- advanced scheduling and heterogeneous optimization
