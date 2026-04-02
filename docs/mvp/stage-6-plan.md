# Stage 6 Plan Tracker

Stage 6 is implemented in the repository as of April 2, 2026. This file remains the canonical scope and acceptance tracker for the stage.

## Stage objective

Build the first stable local demo environment for the distributed training marketplace.

Stage 6 must deliver:

- a usable docker-compose based local environment;
- reliable startup of multiple nodes and supporting services;
- a reproducible demonstration scenario;
- clear demo documentation and helper commands/scripts.

## Stage 6 target result

At the end of Stage 6, the repository must provide a local demo stand in which a developer can:

1. start the demo stack with Docker Compose;
2. run or seed a funded job;
3. observe multiple trainer nodes and at least one evaluator node come online;
4. trigger the end-to-end training protocol flow;
5. observe aggregation and evaluation complete;
6. see the job end in `ready_for_attestation` or `evaluation_failed`;
7. inspect logs, artifacts, round state, and task state locally.

This stage is about reproducibility and demo operability.
It is not about adding new protocol theory or blockchain settlement features.

---

## Codex guardrails for Stage 6

- Do not change the Stage 1 smart-contract model.
- Do not redesign the Stage 5 protocol plugin unless a hard blocker is proven.
- Do not turn this stage into production DevOps or cloud deployment work.
- Do not introduce Kubernetes, Terraform, remote orchestration, or managed services.
- Do not build UI.
- Do not widen the stage into attestation submission or settlement execution.
- Prefer one clean, deterministic local demo path over many partially working variants.

---

## Stage boundaries

### Stage 6 includes

- compose stack consolidation;
- multi-service startup reliability;
- helper scripts for local demo execution;
- seeded demo path;
- clearer environment/config management;
- demo smoke verification;
- docs for reproducing the run.

### Stage 6 explicitly does NOT include

- production deployment architecture;
- Kubernetes or Helm charts;
- cloud-hosted demo infrastructure;
- on-chain attestation submission;
- settlement execution;
- protocol redesign;
- trustless verification;
- UI/dashboard work.

---

## Tracks

### Track 1. Canonical Docker Compose demo stack

Establish one canonical local demo stack.

Tasks:
- review `compose.demo.yml` and `compose.dev.yml`;
- choose one canonical Stage 6 demo entrypoint;
- ensure required services are included:
  - anvil
  - postgres
  - orchestrator
  - at least 2 trainer agents
  - at least 1 evaluator agent
- make service naming predictable and consistent.

Requirements:
- compose must be the primary local demo path;
- the canonical file must not depend on hidden manual edits;
- service startup order and dependency assumptions must be documented.

Deliverables:
- canonical compose configuration;
- simplified service layout;
- removal of ambiguity between demo/dev startup paths if needed.

Done when:
- one compose entrypoint can bring up the entire local demo stand.

---

### Track 2. Environment and configuration hardening

Make demo configuration explicit and reproducible.

Tasks:
- review all `.env.example` files;
- ensure every required service variable is documented;
- ensure defaults are valid for local demo use;
- minimize surprising environment coupling between services.

Required configuration areas:
- RPC URL
- chain ID
- contract address
- database URL
- artifact storage path
- trainer node IDs / ports
- evaluator node IDs / ports
- protocol defaults
- local workspace paths

Deliverables:
- clean env examples;
- demo-ready defaults;
- documented config matrix.

Done when:
- a new developer can configure the demo without guessing hidden settings.

---

### Track 3. Bootstrap and orchestration helper scripts

The demo must not require manual low-level ceremony for every run.

Tasks:
- add helper scripts for:
  - stack startup
  - contract deployment
  - DB migration
  - job seeding / sync
  - protocol run start
  - round reconciliation
  - log tailing or status inspection
- decide whether helpers live under `infra/scripts/` or Make targets or both;
- keep scripts deterministic and readable.

Recommended helper commands:
- `demo-up`
- `demo-init`
- `demo-seed-job`
- `demo-start-flow`
- `demo-status`
- `demo-down`
- `demo-clean`

Deliverables:
- scripts and/or Make targets for the canonical Stage 6 demo path.

Done when:
- the demo can be run with a short, repeatable command sequence.

---

### Track 4. Service readiness and health checks

The stack must be resilient enough for a live demo.

Tasks:
- add or improve service health checks;
- ensure services fail fast on broken startup config;
- ensure orchestrator waits for DB readiness as needed;
- ensure agents tolerate orchestrator startup timing.

Required health surfaces:
- orchestrator `/health`
- orchestrator `/status`
- trainer `/health`
- trainer `/status`
- evaluator `/health`
- evaluator `/status`

Recommended Docker features:
- healthcheck blocks
- restart policy if appropriate for demo stability
- explicit port mapping
- named volumes for local persistence when useful

Deliverables:
- health-aware compose configuration;
- documented expectations for service readiness.

Done when:
- the demo stack starts reliably without race-condition-heavy manual retries.

---

### Track 5. Demo data and seeded scenario hardening

Stage 5 already has an end-to-end protocol flow.
Stage 6 must make that flow easy to demonstrate.

Tasks:
- define one canonical demo scenario;
- make sure the demo job and protocol flow can be seeded reproducibly;
- decide whether job creation is:
  - imported/synced from chain events, or
  - seeded locally in a controlled demo step;
- ensure the demo uses deterministic trainer/evaluator counts and predictable state transitions.

Recommended canonical scenario:
- funded job available locally;
- two trainer nodes online;
- one evaluator node online;
- one round of `fedavg_like_v1`;
- successful aggregation;
- evaluation completes;
- final state visible in orchestrator APIs.

Deliverables:
- one documented canonical demo scenario;
- optional alternate failure scenario only if low-cost.

Done when:
- the same demo outcome can be reproduced consistently.

---

### Track 6. Observability and inspection

A demo stand must be inspectable.

Tasks:
- make it easy to inspect:
  - job state
  - round state
  - trainer tasks
  - evaluation tasks
  - artifacts
  - logs
- add or refine routes/scripts for inspection if needed;
- ensure logs are understandable during a live run.

Recommended inspection surfaces:
- `/jobs`
- `/jobs/{id}`
- `/rounds`
- `/rounds/{id}`
- trainer/evaluator `/status`
- internal protocol/round actions
- artifact metadata access

Deliverables:
- documented inspection commands;
- if necessary, small helper script for status snapshots.

Done when:
- a developer can understand what is happening during the demo without opening the database manually.

---

### Track 7. Demo execution flow documentation

This is the most visible Stage 6 deliverable.

Tasks:
- rewrite `docs/setup/local-demo.md` around the canonical flow;
- include:
  - prerequisites
  - startup
  - initialization
  - job/protocol trigger
  - verification steps
  - cleanup
- keep instructions short enough for a live presentation but detailed enough for reproducibility.

Recommended structure:
1. prerequisites
2. start stack
3. initialize chain + DB
4. verify service health
5. seed/sync funded job
6. start protocol run
7. reconcile round
8. inspect final state
9. cleanup

Deliverables:
- updated `docs/setup/local-demo.md`;
- demo section in root README.

Done when:
- another developer can run the demo from docs alone.

---

### Track 8. Demo smoke automation

Add one smoke path that proves the stack is runnable.

Tasks:
- add one automated smoke verification path for Stage 6;
- it may be a script, Make target, or integration test;
- it must verify that the demo stand is not merely bootable but operational.

Smoke validation should cover:
- services come online;
- protocol run can be triggered;
- at least one round is created;
- trainer tasks are completed;
- evaluation completes;
- final lifecycle outcome is observable.

Deliverables:
- Stage 6 smoke script/test;
- documented expected outputs.

Done when:
- the local demo stand can be validated quickly before presentation.

---

### Track 9. Cleanup and consolidation

By Stage 6, the repository may have overlapping helper paths.
Clean them up.

Tasks:
- remove or clearly de-emphasize obsolete manual demo paths if they confuse the canonical flow;
- reduce duplicate commands and scripts;
- ensure docs and Make targets point to the same preferred path.

Deliverables:
- cleaner demo-oriented repository experience.

Done when:
- there is one obvious way to run the local demo.

---

## File and module expectations

Stage 6 is expected to create or significantly expand files in these areas.

### Infra
- `infra/compose/compose.demo.yml`
- `infra/compose/compose.dev.yml` if still needed
- `infra/env/*.env.example`
- `infra/scripts/*`

### Docs
- `docs/mvp/stage-6-plan.md`
- `docs/setup/local-demo.md`
- `docs/setup/development.md`
- `docs/codex/AGENTS-STAGE6-ADDENDUM.md` if used

### Root/project helpers
- `Makefile`
- `README.md`

### Optional small API/support additions
Only if needed for demo inspection or initialization:
- orchestrator internal routes
- round inspection routes
- demo seeding helpers

---

## Recommended order of implementation

1. choose the canonical compose entrypoint;
2. harden environment defaults;
3. add helper scripts / Make targets;
4. add health checks and startup coordination;
5. define the canonical seeded demo scenario;
6. document the exact run flow;
7. add smoke verification;
8. clean up duplicate/obsolete demo paths.

Do not start redesigning protocol/runtime internals unless the demo environment exposes a real blocker.

---

## Explicit non-goals for Stage 6

Do NOT implement in this stage:
- cloud deployment;
- production orchestration infrastructure;
- Kubernetes;
- on-chain attestation submission;
- settlement execution;
- protocol redesign;
- advanced protocol experimentation;
- UI.

These belong to later stages.

---

## Acceptance criteria

Stage 6 is complete only if all of the following are true:

1. there is one canonical compose-based local demo path;
2. the local demo stand includes multiple trainer nodes and at least one evaluator node;
3. the demo stack can be started reproducibly from documented commands;
4. helper commands/scripts cover startup, initialization, run, inspection, and cleanup;
5. service health and readiness are observable;
6. a funded job can be seeded or synchronized into the local demo;
7. the Stage 5 protocol flow can be demonstrated in the local stand;
8. the final lifecycle outcome is observable through documented inspection steps;
9. another developer can reproduce the demo from docs alone;
10. Stage 6 does not widen into production infrastructure or later blockchain stages.

---

## Completion summary format

When Stage 6 is done, update this file with:

## Stage 6 implementation status
- Canonical compose stack: complete
- Environment/config hardening: complete
- Bootstrap/helper scripts: complete
- Service readiness and health checks: complete
- Canonical demo scenario: complete
- Observability and inspection flow: complete
- Demo documentation: complete
- Demo smoke verification: complete
- Cleanup/consolidation: complete

## Delivered behavior
Stage 6 delivers a reproducible local demo stand for the distributed training marketplace, including multiple trainers, at least one evaluator, deterministic startup/configuration, helper scripts, and a documented end-to-end demonstration path.
