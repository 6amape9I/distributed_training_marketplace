# AGENTS Stage 4 Addendum

## Purpose of Stage 4

Stage 4 introduces the first real evaluation flow.

The goal is not to finish settlement or on-chain attestation.
The goal is to make evaluator nodes real:
- register with the orchestrator,
- stay online via heartbeat,
- claim evaluation tasks,
- compute metrics on produced model artifacts,
- upload evaluation reports,
- move lifecycle state forward.

Stage 3 already delivered trainer execution, training tasks, artifacts, and local model outputs. Stage 4 must build on that instead of redesigning it.

---

## What must remain true

1. Do not change the Stage 1 smart-contract model.
2. Do not break the Stage 2 orchestrator core.
3. Do not redesign the Stage 3 trainer/task/artifact flow unless a real blocker is proven.
4. Keep evaluation logic separate from trainer logic.
5. Keep metrics and report generation off-chain.
6. Keep evaluation generic enough for later protocol changes.

---

## Stage 4 is successful only if

- evaluator agents are no longer placeholders;
- evaluators register and send heartbeats;
- evaluators can claim real evaluation tasks;
- evaluators compute real metrics;
- evaluators upload report artifacts;
- orchestrator stores evaluation reports;
- lifecycle reacts to completed evaluation.

If there is no real metric computation and no real lifecycle impact, Stage 4 is not complete.

---

## What not to do

Do not:
- push training-result attestations on-chain;
- redesign settlement;
- implement slashing, reputation, or trustless verification;
- build a final aggregation framework as a product feature;
- add UI;
- mix evaluator code into trainer runtime;
- hide evaluation behavior inside ad hoc scripts instead of services.

If implementation drifts into blockchain finalization, contribution accounting, or advanced validation theory, it has left Stage 4.

---

## Architecture rules

### 1. Evaluator logic must be isolated
Transport, task claiming, metric execution, report generation, and artifact upload must be separate concerns.

Expected separations:
- orchestrator client
- evaluation task polling / claiming
- metric executor
- report builder
- artifact uploader / repository
- heartbeat worker

### 2. Reuse Stage 3 artifacts instead of bypassing them
Evaluator flow must consume trainer-produced artifact references through orchestrator-controlled APIs.
Do not invent side channels or direct hidden file-path coupling between trainer and evaluator services.

### 3. Metric logic must stay in execution layer
Routes and transport code must not contain metric math.
Metric computation belongs in evaluator execution services.

### 4. Lifecycle updates must stay orchestrator-driven
Evaluator agents produce reports.
The orchestrator owns lifecycle transitions.

Do not let evaluator runtime mutate lifecycle state directly outside orchestrator APIs.

---

## Preferred implementation bias

When choosing between:
- a smaller real evaluation flow, and
- a larger fake framework,

choose the smaller real flow.

Examples:
- better: one real evaluation task type with real metrics
- worse: many abstract evaluator modes with no real execution

- better: deterministic demo metric computation
- worse: vague placeholder “score” values

- better: explicit report artifact upload
- worse: embedding all evaluation output only in DB rows without a real report artifact

---

## Required implementation style

- Keep route handlers thin.
- Put business logic in application services.
- Keep DB-backed state authoritative.
- Make failure paths explicit:
  - claim failure
  - artifact read failure
  - metric execution failure
  - report upload failure
  - completion failure

An evaluation task must be able to end in `failed` cleanly.

---

## Required testing focus

Tests must prove:
- evaluator claim semantics are safe enough for Stage 4;
- evaluator computes real metrics on demo artifacts;
- report artifacts are persisted;
- lifecycle changes after evaluation completion;
- Stage 3 trainer outputs are usable as Stage 4 evaluation inputs.

Do not rely only on route smoke tests.

---

## Required delivery discipline

When committing Stage 4 work:
- keep commits scoped by track where possible;
- do not mix evaluator runtime, lifecycle changes, and docs into one unclear commit if avoidable;
- update docs as behavior stabilizes;
- document any design choice that affects Stage 5+.

If a proposed change impacts trainer task model, artifact model, or lifecycle semantics broadly, document why before widening the change.

---

## Escalation rule

If Stage 4 appears to require:
- contract changes,
- blockchain writes,
- production aggregation design,
- trustless verification,
- evaluator/trainer architecture merge,

stop and document the blocker before proceeding.

Do not quietly widen the stage.

---

## Final reminder

Stage 4 is about proving that evaluation is a real off-chain flow.

A good Stage 4 gives us:
- real evaluator nodes,
- real evaluation tasks,
- real metric computation,
- real evaluation reports,
- real lifecycle progress.

That is enough.