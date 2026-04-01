# AGENTS Stage 3 Addendum

## Purpose of Stage 3

Stage 3 introduces the first real off-chain execution path.

The goal is not to finish the marketplace.
The goal is to make trainer agents real:
- register with the orchestrator,
- stay online via heartbeat,
- claim training tasks,
- execute local training,
- upload artifacts,
- report completion.

Stage 2 already delivered the orchestrator core and explicitly deferred real training, datasets, artifact movement, and task dispatch to Stage 3 :contentReference[oaicite:0]{index=0}

---

## What must remain true

1. Do not change the Stage 1 smart-contract model.
2. Do not break Stage 2 orchestrator boundaries.
3. Do not hardwire the whole project to FedAvg naming or assumptions.
4. Keep training execution generic enough to support later protocol changes.
5. Keep blockchain concerns out of trainer execution logic.
6. Keep artifacts off-chain.

---

## Stage 3 is successful only if

- trainer agents are no longer health-only placeholders;
- trainers register and send heartbeats;
- trainers can claim real tasks;
- trainers execute real local training;
- trainers upload output artifacts;
- multiple trainer processes can run concurrently;
- the flow is reproducible locally.

If there is no real task execution and no real artifact output, Stage 3 is not complete.

---

## What not to do

Do not:
- implement evaluator execution;
- implement final aggregation as a product feature;
- redesign job settlement;
- redesign contract events;
- add UI;
- add P2P networking;
- add reputation, slashing, Byzantine handling, or trustless verification;
- overbuild a general distributed training framework.

If implementation drifts into evaluator logic, global model finalization, or advanced protocol theory, it has left Stage 3.

---

## Architecture rules

### 1. Trainer logic must be isolated
Transport, orchestration API calls, training execution, and artifact storage must be separate concerns.

Expected separations:
- orchestrator client
- task polling / claiming
- task executor
- artifact uploader / repository
- heartbeat worker

### 2. Task model must stay generic
Prefer names like:
- training task
- local_fit
- task result
- trainer report

Avoid baking protocol-specific assumptions into core schemas unless unavoidable.

### 3. Dataset and model assumptions must stay inside the demo execution layer
It is acceptable to use a tiny dataset and a small model for Stage 3, but those choices must not leak into the repository-wide architecture.

### 4. Trainer processes must be independently runnable
Each trainer must have its own:
- node id
- workspace
- heartbeat loop
- task execution context

No fake “multi-trainer” implementation inside one process pretending to be several nodes.

---

## Preferred implementation bias

When choosing between:
- a smaller real flow, and
- a larger fake flow,

choose the smaller real flow.

Examples:
- better: one real task type (`local_fit`)
- worse: many task types with no real execution

- better: local filesystem artifact repository that really stores outputs
- worse: abstract artifact system with no actual files saved

- better: two or three real trainer processes
- worse: one process simulating many without independent registration

---

## Required implementation style

- Favor simple, explicit services over clever abstractions.
- Keep route handlers thin.
- Put business logic in application services.
- Keep DB-backed state authoritative for orchestrator task state.
- Make failure paths explicit:
  - claim failure
  - upload failure
  - execution failure
  - report failure

A task must be able to end in `failed` cleanly.

---

## Required testing focus

Tests must prove:
- task claim semantics are safe enough for Stage 3;
- trainers can complete tasks end-to-end;
- artifact metadata is persisted;
- task outputs are not just mocked strings pretending to be training;
- multi-trainer local flow works at least in a controlled demo/test scenario.

Do not rely only on route smoke tests.

---

## Required delivery discipline

When committing Stage 3 work:
- keep commits scoped by track;
- do not mix trainer runtime, DB schema, and docs into one giant unclear commit if avoidable;
- update docs as the implementation stabilizes, not only at the very end.

If a design change affects Stage 4+, mention it explicitly in docs or commit notes.

---

## Escalation rule

If Stage 3 appears to require:
- contract changes,
- evaluator implementation,
- full aggregation logic,
- protocol redesign,

stop and document the blocker before proceeding.

Do not quietly widen the stage.

---

## Final reminder

Stage 3 is about proving that trainer nodes are real workers, not placeholders.

A good Stage 3 gives us:
- real nodes,
- real tasks,
- real local training,
- real artifact outputs.

That is enough.