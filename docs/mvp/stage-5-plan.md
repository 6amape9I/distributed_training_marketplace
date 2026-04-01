# Stage 5 Plan Tracker

Stage 5 is implemented in the repository as of April 1, 2026. This file remains the canonical scope and acceptance tracker for the stage.

## Stage objective

Implement the first real training protocol plugin (`v1`) for the distributed training marketplace.

Stage 5 must deliver:

- the first protocol plugin based on a FedAvg-like flow;
- orchestrator-side round coordination for that plugin;
- trainer task generation driven by the protocol plugin rather than by ad hoc demo seeding;
- model update collection and aggregation;
- evaluation trigger after aggregation;
- an end-to-end distributed training flow.

## Stage 5 target result

At the end of Stage 5, the repository must contain a working end-to-end distributed training path:

1. a funded job reaches the scheduling/running phase;
2. the orchestrator creates round work through a real protocol plugin;
3. multiple trainer nodes execute `local_fit` tasks against the same base model and different data partitions;
4. trainer outputs are collected and aggregated into a new model artifact;
5. evaluator flow is triggered on the aggregated model;
6. evaluation reports affect lifecycle state;
7. the system reaches `ready_for_attestation` or `evaluation_failed` through a real plugin-driven run.

This stage does NOT need to perform on-chain attestation submission or final settlement.

---

## Codex guardrails for Stage 5

- Do not change the Stage 1 contract model.
- Do not collapse the architecture into a permanently FedAvg-specific system.
- FedAvg-like is the first plugin, not the final architecture.
- Do not bypass Stage 3/4 task and artifact flows.
- Do not implement on-chain writes from training/evaluation outputs.
- Do not implement trustless verification, slashing, reputation, or Byzantine defenses.
- Do not redesign evaluator flow into a broader research framework.
- Keep protocol logic in a plugin boundary, not scattered across route handlers and unrelated services.

---

## Stage boundaries

### Stage 5 includes

- protocol plugin abstraction finalized enough for `v1`;
- one concrete plugin implementation: `fedavg_like_v1`;
- round-oriented orchestration;
- base model artifact publication;
- multi-trainer task fan-out for one round;
- aggregation of trainer-produced model updates into a new model artifact;
- evaluation seeding from the aggregated model;
- lifecycle progression through a complete off-chain run.

### Stage 5 explicitly does NOT include

- on-chain attestation submission;
- settlement execution;
- contribution scoring and payout refinement;
- trustless verification;
- robust Byzantine-resistant aggregation;
- advanced peer-to-peer coordination;
- advanced multi-round optimization research;
- production FL framework breadth.

---

## Tracks

### Track 1. Protocol plugin architecture hardening

Stage 3 and Stage 4 introduced trainer and evaluator flows. Stage 5 must now put a real protocol boundary around them.

Tasks:
- formalize the `TrainingProtocol` interface;
- define plugin responsibilities;
- define plugin inputs/outputs;
- make orchestrator depend on the protocol plugin rather than direct demo dispatch logic.

Minimum plugin responsibilities:
- create round plan;
- seed trainer work for a round;
- define aggregation inputs;
- publish aggregated model artifact;
- request evaluation for the aggregated artifact;
- recommend lifecycle transitions to orchestration services.

Recommended plugin-facing structures:
- protocol run context
- round plan
- aggregation input set
- aggregation result
- evaluation request context

Deliverables:
- stable protocol plugin interface;
- one concrete plugin registration path;
- documentation on plugin boundaries.

Done when:
- orchestrator can invoke a protocol plugin without hardcoding Stage 3 task seeding logic.

---

### Track 2. Round model introduction

Stage 5 should explicitly model rounds.

Tasks:
- add a round entity and persistence model;
- define round statuses;
- relate rounds to jobs;
- relate training tasks and evaluation tasks to rounds.

Recommended round statuses:
- pending
- seeded
- training
- aggregating
- evaluating
- completed
- failed

Recommended minimum round fields:
- round_id
- job_id
- protocol_name
- round_index
- status
- base_model_artifact_uri
- aggregated_model_artifact_uri
- aggregated_model_artifact_hash
- evaluation_report_id or evaluation summary reference
- created_at
- updated_at

Deliverables:
- round domain entity;
- DB model and migration;
- repository interface + implementation.

Done when:
- the orchestrator can persist and inspect round-level state.

---

### Track 3. FedAvg-like protocol plugin v1

Implement the first plugin.

Scope of the plugin:
- one shared base model artifact;
- N trainer tasks, each training on its own partition;
- one aggregation step that combines trainer outputs;
- one evaluation step on the aggregated model.

Required behavior:
- seed one round for a job;
- distribute one base model to all trainer tasks;
- wait for required trainer completions;
- aggregate trainer results by weighted averaging over `sample_count`;
- publish aggregated model artifact;
- request evaluation for that aggregated model.

Important:
- this is a FedAvg-like plugin, not a complete federated-learning framework;
- aggregation may be simple arithmetic averaging over trainer-produced weights/bias.

Deliverables:
- plugin implementation under orchestrator application layer;
- tests for plugin round orchestration.

Done when:
- a real round can be driven by the plugin end-to-end.

---

### Track 4. Trainer task generation from protocol plugin

Replace ad hoc demo task seeding as the primary execution path.

Tasks:
- add a plugin-driven trainer task seeding service;
- generate trainer tasks from round plan;
- assign shared base model artifact and per-trainer dataset artifacts;
- associate each trainer task with a round.

Requirements:
- task creation must be deterministic for a given job/round setup;
- multiple trainers must receive distinct data partitions;
- task metadata must indicate round membership.

Deliverables:
- protocol-driven task seeding;
- round-linked trainer task records;
- internal orchestration path that no longer depends on manual demo-only seeding.

Done when:
- the orchestrator can create round trainer tasks through the plugin.

---

### Track 5. Aggregation flow

This is the core new capability of Stage 5.

Tasks:
- define aggregation input selection rules;
- load trainer-produced result artifacts;
- parse model outputs;
- average compatible outputs into one aggregated model;
- store the aggregated result as a new model artifact;
- persist aggregation metadata and linkage to the round.

Recommended Stage 5 aggregation scope:
- support the exact model output format produced by `local_fit`;
- average weights and bias across all completed trainer tasks in the round.

Important:
- aggregation logic must be an application/service concern, not route logic;
- keep the interface extensible enough for future aggregation strategies.

Suggested abstraction:
- `AggregationStrategy`
- `FedAvgLikeAggregationStrategy`

Deliverables:
- aggregation service/strategy;
- aggregated model artifact creation;
- tests for numeric aggregation correctness.

Done when:
- a completed set of trainer task outputs can become one aggregated model artifact.

---

### Track 6. Evaluation trigger from aggregated model

Stage 4 already implemented evaluator flow. Stage 5 must connect it to real aggregated outputs.

Tasks:
- seed evaluation tasks from aggregated round model, not directly from per-trainer outputs;
- ensure evaluation targets the aggregated artifact;
- connect evaluation completion back to the round and job lifecycle.

Recommended behavior:
- one evaluation task per round aggregated model;
- use the Stage 4 evaluation manifest flow or a round-aware equivalent.

Deliverables:
- evaluation seeding path from aggregated model artifact;
- round/job linkage updates.

Done when:
- aggregated model evaluation is part of the end-to-end flow.

---

### Track 7. Lifecycle integration for full training flow

Stage 5 must connect scheduling, training, aggregation, evaluation, and completion into one orchestrated path.

Tasks:
- extend lifecycle handling to include round progression;
- define how trainer completion triggers aggregation readiness;
- define how successful aggregation triggers evaluation;
- define how evaluation completion changes round/job state.

Recommended additions if needed:
- round-level reconciliation service;
- orchestration coordinator updates;
- “run once” internal orchestration method covering:
  - seed round
  - detect trainer completion
  - aggregate
  - seed evaluation
  - reconcile completion

Deliverables:
- lifecycle orchestration for Stage 5 flow;
- tests for status progression across the full run.

Done when:
- one complete off-chain training cycle can advance job state without manual patching of state.

---

### Track 8. Internal orchestration APIs / run controls

Add controlled internal endpoints or scripts for Stage 5 orchestration.

Implemented endpoints:
- POST /internal/protocol-runs/start-for-job/{job_id}
- POST /internal/rounds/{round_id}/reconcile
- GET /jobs/{job_id}/rounds
- GET /rounds/{round_id}

These do not need to be public product APIs.
They are acceptable as internal orchestration controls for MVP.

Deliverables:
- internal control path for Stage 5 demo;
- docs for the intended execution sequence.

Done when:
- developers can drive a full plugin-based run without editing DB rows manually.

---

### Track 9. End-to-end demo flow

This is the acceptance core of Stage 5.

Tasks:
- update demo docs and compose workflow;
- ensure the local stack supports:
  - orchestrator
  - at least 2 trainer agents
  - at least 1 evaluator agent
- document the full execution path from job sync/seed to final lifecycle outcome.

Minimum demo sequence:
1. sync/import funded job;
2. register online trainers and evaluator;
3. run lifecycle reconcile until the job reaches `scheduling`;
4. start the protocol run for the job;
5. trainers complete local tasks;
6. orchestrator reconciles the round into aggregation and evaluation;
7. evaluator evaluates the aggregated model;
8. orchestrator reconciles the round into a final lifecycle outcome.

Deliverables:
- reproducible local demo instructions;
- if helpful, helper script for one-command smoke flow.

Done when:
- the repository demonstrates a real end-to-end distributed training flow.

---

### Track 10. Testing

Stage 5 must add the strongest test layer so far.

Required test areas:
- protocol plugin behavior;
- round seeding;
- aggregation correctness;
- aggregated-model evaluation trigger;
- lifecycle progression across the full Stage 5 run;
- failure handling if a trainer task fails or aggregation inputs are incomplete.

Recommended tests:
- unit tests:
  - FedAvg-like aggregation
  - round planning
  - protocol plugin orchestration decisions
- integration tests:
  - end-to-end orchestrator flow with fake or test runtimes
  - trainer outputs -> aggregation -> evaluator task seeding
  - final lifecycle state transition
- smoke tests:
  - local multi-trainer + evaluator demo

Deliverables:
- expanded pytest coverage for Stage 5;
- at least one full flow test proving end-to-end behavior.

Done when:
- Stage 5 is proven by tests, not only by documentation.

---

### Track 11. Documentation update

Tasks:
- update README current stage summary;
- add Stage 5 quick start;
- document round model;
- document protocol plugin v1 behavior;
- document aggregation assumptions and limitations;
- document what remains deferred to Stage 6.

Deliverables:
- updated setup docs;
- updated local demo docs;
- stage-5-plan tracker committed.

Done when:
- a new developer can reproduce the Stage 5 flow locally.

---

## File and module expectations

Stage 5 is expected to create or significantly expand files in these areas.

### Orchestrator
- orchestrator/app/application/protocols/training_protocol.py
- orchestrator/app/application/services/protocol_runner.py
- orchestrator/app/application/services/round_seeding_service.py
- orchestrator/app/application/services/round_reconcile_service.py
- orchestrator/app/application/services/aggregation_service.py
- orchestrator/app/application/services/fedavg_like_plugin.py
- orchestrator/app/domain/entities/round.py
- orchestrator/app/domain/repositories/round_repository.py
- orchestrator/app/infrastructure/db/models.py
- orchestrator/app/infrastructure/db/repositories.py
- orchestrator/app/api/routes/internal.py
- orchestrator/app/tests/*

### Shared
- shared/python/schemas/round.py
- optional plugin/aggregation-related shared DTOs if truly needed

### Trainer / Evaluator
- mostly reuse existing Stage 3/4 runtime flows;
- only minimal updates if round-aware task handling requires them.

### Docs
- docs/mvp/stage-5-plan.md
- docs/codex/AGENTS-STAGE5-ADDENDUM.md
- docs/setup/local-demo.md
- docs/setup/development.md

---

## Recommended order of implementation

1. introduce round domain model and persistence;
2. harden protocol plugin interface;
3. implement FedAvg-like plugin v1;
4. replace ad hoc trainer task seeding with plugin-driven round seeding;
5. implement aggregation service;
6. connect evaluation seeding to aggregated model;
7. integrate lifecycle/reconciliation;
8. expose internal run controls;
9. add tests;
10. update docs and demo flow.

Do not jump to on-chain attestation or payout logic before the end-to-end off-chain flow is stable.

---

## Explicit non-goals for Stage 5

Do NOT implement in this stage:
- on-chain attestation submission;
- settlement execution;
- contribution scoring;
- slashing or reputation;
- trustless verification;
- Byzantine-resistant aggregation research;
- production FL generality;
- UI.

These belong to later stages.

---

## Acceptance criteria

Stage 5 is complete only if all of the following are true:

1. the repository has a real protocol plugin abstraction;
2. a concrete FedAvg-like plugin v1 is implemented;
3. round state is persisted and observable;
4. multiple trainer tasks are created by the plugin for the same round;
5. trainer outputs are aggregated into a new model artifact;
6. evaluator flow runs on the aggregated model artifact;
7. lifecycle advances through the end-to-end off-chain flow;
8. the final outcome is `ready_for_attestation` or `evaluation_failed`;
9. the flow is reproducible locally;
10. the implementation remains extensible for future non-FedAvg protocols.

---

## Completion summary format

When Stage 5 is done, update this file with:

## Stage 5 implementation status
- Protocol plugin architecture: complete
- Round model: complete
- FedAvg-like plugin v1: complete
- Plugin-driven trainer task seeding: complete
- Aggregation flow: complete
- Evaluation trigger from aggregated model: complete
- Lifecycle integration: complete
- Internal orchestration controls: complete
- End-to-end demo: complete
- Tests: complete
- Documentation: complete

## Delivered behavior
Stage 5 delivers the first real protocol plugin (`fedavg_like_v1`) and a complete end-to-end distributed training flow in which the orchestrator seeds a round, multiple trainers produce updates, outputs are aggregated into a new model artifact, evaluator flow runs on that aggregated model, and job lifecycle reaches a real post-evaluation outcome without changing the trust-layer contract model.
