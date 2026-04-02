# AGENTS Stage 6 Addendum

## Purpose of Stage 6

Stage 6 is about demo operability.

The goal is not to invent new protocol logic.
The goal is not to build production infrastructure.
The goal is to make the existing system easy to run, inspect, and demonstrate locally.

A good Stage 6 gives us:
- one obvious way to start the stack,
- one obvious way to initialize it,
- one obvious way to run the demo,
- one obvious way to verify the outcome.

---

## What must remain true

1. Do not change the Stage 1 smart-contract model.
2. Do not redesign the Stage 5 protocol plugin unless a real blocker is proven.
3. Keep the local demo path centered on Docker Compose.
4. Keep all model execution, aggregation, and evaluation off-chain.
5. Keep the demo deterministic and reproducible.
6. Prefer one canonical demo path over many partially maintained alternatives.

---

## Stage 6 is successful only if

- the stack can be started reliably;
- multiple trainers and at least one evaluator come online;
- the demo run is reproducible from docs/scripts;
- health and status can be inspected clearly;
- another developer can run the demo without guessing hidden steps.

If the repository still requires ad hoc manual steps scattered across chat history or tribal knowledge, Stage 6 is not complete.

---

## What not to do

Do not:
- introduce Kubernetes, Helm, Terraform, or cloud deployment work;
- redesign protocol logic just because a demo script exposed inconvenience;
- add UI;
- widen the stage into on-chain attestation or settlement;
- create many competing startup paths without choosing a canonical one;
- hide critical demo logic in opaque shell one-liners without documentation.

If implementation drifts into production DevOps or later blockchain stages, it has left Stage 6.

---

## Architecture rules

### 1. Demo environment must wrap the existing architecture, not replace it
Compose, scripts, and helpers should orchestrate:
- anvil
- postgres
- orchestrator
- trainers
- evaluator

They must not fork or bypass the actual Stage 5 flow.

### 2. Prefer explicit scripts over fragile manual ceremony
A smaller number of clear helper commands is better than expecting the operator to remember a long undocumented sequence.

### 3. Health and readiness matter
For a demo, startup stability is part of functionality.
If the stack starts unreliably, Stage 6 is not done.

### 4. Documentation is a first-class deliverable
If a workflow exists but is not written down clearly, treat it as incomplete.

---

## Preferred implementation bias

When choosing between:
- a smaller but highly reproducible local demo path, and
- a broader but fragile environment matrix,

choose the smaller reproducible path.

Examples:
- better: one canonical `compose.demo.yml`
- worse: several overlapping compose variants with unclear status

- better: one documented init/run/cleanup flow
- worse: multiple partially working command sequences

- better: one smoke script that proves the stand works
- worse: many docs claims with no verification path

---

## Required implementation style

- Keep helper scripts readable and explicit.
- Keep docs aligned with actual commands in the repository.
- Keep service names and ports consistent.
- Fail early on missing config.
- Make cleanup easy.
- Preserve inspectability:
  - health
  - status
  - rounds
  - jobs
  - tasks
  - artifacts
  - logs

---

## Required testing focus

Tests or smoke validation must prove:
- the local stand is bootable;
- core services become reachable;
- the Stage 5 flow can be exercised in the local environment;
- final demo state can be observed without manual DB inspection.

Do not rely only on “compose up succeeds” as proof of completeness.

---

## Required delivery discipline

When committing Stage 6 work:
- keep infrastructure changes scoped where possible;
- update docs together with script changes;
- remove or de-emphasize obsolete demo paths if a new canonical one is chosen;
- document assumptions about ports, addresses, and local persistence.

If a script becomes the preferred entrypoint, the docs must say so clearly.

---

## Escalation rule

If Stage 6 appears to require:
- protocol redesign,
- contract changes,
- on-chain writes,
- production deployment tooling,
- major trainer/evaluator rewrites,

stop and document the blocker before proceeding.

Do not quietly widen the stage.

---

## Final reminder

Stage 6 is about credibility in execution.

A good Stage 6 lets someone clone the repository, follow the docs, bring up the local stack, run the demo, and see the result.

That is enough.