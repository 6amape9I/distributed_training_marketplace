# AGENTS Stage 5 Addendum

## Purpose of Stage 5

Stage 5 introduces the first real protocol plugin and the first real end-to-end distributed training flow.

The goal is not to finish the blockchain side.
The goal is not to build a full federated-learning platform.
The goal is to connect the existing parts into one coherent off-chain run:

- orchestrator
- trainers
- aggregation
- evaluator
- lifecycle progression

A good Stage 5 proves that the marketplace can execute one complete distributed training cycle.

---

## What must remain true

1. Do not change the Stage 1 smart-contract model.
2. Do not bypass Stage 3 trainer task flow.
3. Do not bypass Stage 4 evaluator flow.
4. Keep all model execution, aggregation, and metrics off-chain.
5. FedAvg-like is a plugin choice, not the permanent architecture.
6. Round logic must not be smeared across unrelated services and route handlers.

---

## Stage 5 is successful only if

- there is a real protocol plugin abstraction;
- one concrete plugin (`FedAvg-like v1`) works;
- multiple trainer outputs are aggregated into a new model artifact;
- evaluator flow runs on that aggregated model;
- lifecycle moves through a full off-chain run;
- the repository demonstrates an end-to-end distributed training flow.

If the system still depends on manual ad hoc task seeding without plugin-driven orchestration, Stage 5 is not complete.

---

## What not to do

Do not:
- implement on-chain attestation submission;
- implement settlement execution;
- add contribution scoring or reward formulas;
- add slashing, reputation, or trustless verification;
- redesign the contract layer;
- turn the project into a broad research framework with many unfinished protocol variants;
- push UI work.

If implementation drifts into settlement, tokenomics, or anti-Byzantine research, it has left Stage 5.

---

## Architecture rules

### 1. Protocol logic must live behind a plugin boundary
Do not scatter FedAvg-like decisions across:
- routes
- random orchestration helpers
- trainer runtime
- evaluator runtime

The orchestrator should call a protocol plugin / protocol runner.

### 2. Round state must be explicit
Do not fake rounds through task-name conventions alone.
If the system is coordinating distributed training, it must persist and expose round state clearly.

### 3. Aggregation must stay isolated
Aggregation is a separate concern from:
- trainer execution
- evaluator execution
- artifact transport
- lifecycle rules

Treat it as a service or strategy, not a side effect hidden inside unrelated code.

### 4. Trainer and evaluator runtimes should require only minimal changes
Most Stage 5 work belongs in the orchestrator and protocol layer.
Do not rewrite trainer/evaluator architecture unless there is a real blocker.

### 5. Demo assumptions must stay contained
It is acceptable to keep the first plugin numerically simple and model-format-specific.
It is not acceptable to leak demo-only assumptions into the whole architecture without boundaries.

---

## Preferred implementation bias

When choosing between:
- a smaller real end-to-end flow, and
- a larger fake “framework”,

choose the smaller real flow.

Examples:
- better: one real round model and one real FedAvg-like plugin
- worse: several “future plugin” stubs with no complete flow

- better: simple averaging over the exact trainer output schema we already have
- worse: abstract aggregation system with no real aggregated model produced

- better: one deterministic end-to-end run that reaches `ready_for_attestation` or `evaluation_failed`
- worse: many disconnected partial orchestration paths

---

## Required implementation style

- Keep route handlers thin.
- Keep orchestration decisions in application services.
- Make round and lifecycle transitions explicit.
- Make failure states explicit:
  - incomplete trainer set
  - malformed trainer output
  - aggregation failure
  - evaluation seeding failure
  - evaluator rejection
- Prefer deterministic demo behavior over clever hidden automation.

A round must be able to fail cleanly.

---

## Required testing focus

Tests must prove:
- multiple trainer outputs are actually aggregated;
- aggregated artifact is a real new model artifact;
- evaluator flow targets the aggregated artifact rather than individual trainer outputs;
- lifecycle changes after evaluation of the aggregated model;
- one end-to-end distributed run works from trainer tasks to post-evaluation state.

Do not rely only on route smoke tests or “service exists” tests.

---

## Required delivery discipline

When committing Stage 5 work:
- keep commits scoped by track where possible;
- do not mix round model, aggregation, and docs into one giant unclear commit if avoidable;
- document assumptions of the FedAvg-like plugin;
- clearly note any limitation that should be revisited in Stage 6+.

If a design choice is knowingly demo-specific, say so in docs.

---

## Escalation rule

If Stage 5 appears to require:
- contract changes,
- on-chain writes,
- payout logic redesign,
- trustless verification,
- advanced Byzantine-robust aggregation,
- large changes to trainer/evaluator architecture,

stop and document the blocker before proceeding.

Do not quietly widen the stage.

---

## Final reminder

Stage 5 is the first proof that the pieces actually form a distributed training system.

A good Stage 5 gives us:
- real rounds,
- real plugin-driven trainer work,
- real aggregation,
- real evaluator flow on the aggregated result,
- real lifecycle progression.

That is enough.