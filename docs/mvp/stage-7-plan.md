# Stage 7 Plan Tracker

Stage 7 is planned as the public testnet integration stage for the distributed training marketplace.

## Stage objective

Deploy the trust-layer contracts to a public EVM testnet and verify the full MVP scenario against a public RPC.

Stage 7 must deliver:

- one canonical public testnet target for MVP demonstration;
- repeatable contract deployment to that network;
- public-RPC-aware orchestrator configuration;
- a funded public testnet job flow;
- end-to-end off-chain training against the deployed public contract state;
- on-chain attestation submission;
- on-chain settlement execution using the existing Stage 1 contract model;
- a documented public demonstration path.

## Stage 7 target result

At the end of Stage 7, the repository must provide a public testnet MVP path in which a developer can:

1. deploy `TrainingMarketplace` to the canonical public testnet;
2. configure the orchestrator against a public RPC and the deployed contract address;
3. create and fund a real public testnet job;
4. synchronize that job into the orchestrator;
5. run the existing distributed training flow with multiple trainers and at least one evaluator;
6. observe the job reach `ready_for_attestation` or `evaluation_failed` off-chain;
7. submit the final attestation on-chain when the run succeeds;
8. finalize the job on-chain using the existing settlement model;
9. withdraw provider payout and requester refund on the public testnet;
10. verify the entire scenario from public chain state, orchestrator APIs, and logs.

This stage is about public-chain integration credibility.
It is not about mainnet launch.
It is not about redesigning the protocol or introducing tokenomics.

---

## Codex guardrails for Stage 7

- Do not redesign the Stage 1 contract model unless a hard blocker is proven.
- Do not turn Stage 7 into a broad multi-network deployment matrix.
- Choose one canonical public testnet path for the MVP.
- Keep all model execution, aggregation, and evaluation off-chain.
- Reuse the Stage 5 protocol plugin and Stage 6 demo flow wherever possible.
- Do not introduce UI or wallet-product work.
- Do not widen the stage into reputation, slashing, Byzantine defenses, or trustless verification.
- Prefer one clear public demo path over several partially working network variants.

---

## Stage boundaries

### Stage 7 includes

- selection of one canonical public EVM testnet for MVP demonstrations;
- public testnet deployment scripts and deployment artifacts;
- explicit env/config for public RPC use;
- public contract address management;
- orchestrator synchronization against public chain state;
- on-chain attestation submission using the existing contract methods;
- on-chain finalization and withdrawal flows using the existing contract methods;
- public-demo helper scripts and documentation;
- a public testnet verification checklist.

### Stage 7 explicitly does NOT include

- mainnet deployment;
- custom chain / rollup / appchain work;
- token launch or new tokenomics;
- UI/dashboard work;
- production cloud infrastructure;
- Kubernetes / Helm / Terraform;
- trustless verification;
- reputation or slashing systems;
- protocol redesign beyond what is required for integration;
- advanced adversarial-node defenses.

---

## Canonical network decision

Stage 7 should define one canonical public testnet path for the MVP.

Selected default:
- `Base Sepolia` as the canonical Stage 7 target.

Repository requirements:
- the network must be selected explicitly in docs and env examples;
- RPC URL, chain ID, and contract address must be configurable;
- the rest of the architecture must remain network-agnostic enough to support future testnets if needed.

Done when:
- there is one obvious network and one obvious way to run the public demo.

---

## Tracks

### Track 1. Canonical public network and demo scope

The project already has a canonical local demo path.
Stage 7 must now define one canonical public demo path.

Tasks:
- choose the canonical public testnet;
- document why it is the default Stage 7 target;
- define the exact public MVP scenario;
- decide which steps remain manual and which are scriptable.

Canonical Stage 7 scenario should include:
- deployed marketplace contract;
- one funded job on the public testnet;
- one orchestrator connected to the public RPC;
- at least 2 trainer agents;
- at least 1 evaluator agent;
- one complete distributed training run;
- one successful on-chain attestation + finalization path.

Deliverables:
- canonical network decision in docs;
- public demo scenario definition.

Done when:
- the repository has one explicit public-demo target instead of vague “works on some testnet” claims.

---

### Track 2. Public environment and configuration hardening

Stage 6 standardized local demo config.
Stage 7 must standardize public testnet config.

Tasks:
- review env examples for public-chain use;
- define required variables for public integration;
- separate local-only assumptions from public-network settings;
- document private key handling expectations for testnet use.

Required configuration areas:
- public RPC URL
- chain ID
- deployed contract address
- deployer private key
- requester private key
- provider private key
- attestor private key
- database URL
- artifact storage path
- orchestrator public base URL if needed
- trainer/evaluator public endpoints if cross-machine demo is used
- confirmation / polling settings if needed

Deliverables:
- public-ready env examples;
- public config matrix;
- documented secret-handling rules for testnet keys.

Done when:
- a developer can configure the public demo without reverse-engineering local-only defaults.

---

### Track 3. Public contract deployment path

Stage 6 uses deterministic local deployment.
Stage 7 must add a canonical public deployment workflow.

Tasks:
- add or harden a deployment script for public testnets;
- persist deployment outputs in a reproducible location;
- capture:
  - network name
  - chain ID
  - contract address
  - deployment tx hash
  - deployer address
- document how to verify deployed bytecode and ABI alignment if desired.

Requirements:
- the deployment path must not depend on the local deterministic Anvil address;
- deployment outputs must be easy to reuse by orchestrator and helper scripts;
- the workflow must fail clearly on missing RPC URL or private key.

Deliverables:
- public deployment script(s);
- deployment artifact file(s);
- docs for public deploy.

Done when:
- a fresh contract can be deployed to the canonical public testnet from repository instructions alone.

---

### Track 4. Public job creation and funding flow

Stage 6 seeds a funded job on the local chain.
Stage 7 must make that scenario work on a public testnet.

Tasks:
- add a canonical helper path for creating a public job;
- add a canonical helper path for funding that job;
- ensure `jobSpecHash` and escrow values are reproducible/documented;
- define the role wallet mapping:
  - requester
  - provider
  - attestor

Requirements:
- the public job flow must use the real deployed contract;
- the orchestrator must be able to sync/import the on-chain job afterward;
- the workflow must produce a visible funded job state before off-chain training starts.

Deliverables:
- script or Make target for public job creation/funding;
- docs for expected on-chain state.

Done when:
- a funded public testnet job can be created and observed cleanly.

---

### Track 5. Orchestrator public-chain synchronization hardening

Public RPC introduces different operational assumptions than local Anvil.

Tasks:
- verify the orchestrator can sync from the public contract state;
- harden event polling / state refresh for public-chain latency;
- ensure the repository documents the intended sync trigger path;
- confirm that the orchestrator can move a synced funded job into the Stage 5/6 off-chain flow.

Requirements:
- public sync must not depend on local-chain shortcuts;
- repeated sync attempts must remain safe/idempotent where possible;
- logs must make chain/network context visible.

Deliverables:
- tested public sync path;
- public-ready orchestrator config;
- documented sync flow.

Done when:
- a funded job created on the public testnet is visible and usable inside the orchestrator.

---

### Track 6. Public demo runtime path for trainers and evaluator

The Stage 5/6 off-chain flow must work unchanged in principle, but Stage 7 must prove it against the public trust layer.

Tasks:
- define the supported Stage 7 runtime topology:
  - all workers local to one machine, or
  - orchestrator local + worker services on separate machines, if needed
- verify trainers and evaluator can still register and complete tasks under the public-demo setup;
- ensure no local-demo-only assumptions block public-chain use.

Requirements:
- at least 2 trainer nodes must complete work;
- at least 1 evaluator node must complete work;
- the off-chain result must still reach `ready_for_attestation` or `evaluation_failed`.

Deliverables:
- public-demo runtime instructions;
- proof that Stage 5/6 flow remains valid against public chain state.

Done when:
- the distributed training flow reaches the pre-attestation boundary in the public setup.

---

### Track 7. On-chain attestation submission integration

This is the key new blockchain behavior of Stage 7.

Tasks:
- define the attestation payload source from the off-chain result;
- compute / persist the attestation hash deterministically;
- wire attestation submission into a controlled internal path or helper script;
- ensure the correct attestor key is used;
- document the success and failure path clearly.

Requirements:
- Stage 7 must use the existing contract `submitAttestation` path rather than redesigning the contract;
- attestation submission must be explicit and inspectable;
- repeat submission behavior and failure handling must be documented.

Deliverables:
- attestation submission flow;
- helper command/script;
- docs for verifying the on-chain attestation result.

Done when:
- a successful public run can move from `ready_for_attestation` to on-chain `Attested`.

---

### Track 8. On-chain finalization and settlement execution

Stage 7 should complete the full public MVP lifecycle using the existing contract model.

Tasks:
- define the settlement payload source;
- compute / persist the settlement hash deterministically;
- execute `finalizeJob` on-chain with the attestor role;
- document payout/refund values for the canonical demo scenario;
- add helper paths for provider payout withdrawal and requester refund withdrawal.

Requirements:
- Stage 7 must use the existing settlement structure already supported by the contract;
- settlement values must sum correctly to escrow;
- the workflow must not require UI.

Canonical MVP settlement policy for the success demo path is fixed and deterministic:
- `90%` provider payout on successful demo completion;
- `10%` requester refund remainder;
- if the off-chain run ends in `evaluation_failed`, the canonical Stage 7 path stops before attestation and finalization.

Deliverables:
- finalization helper flow;
- payout/refund withdrawal helper flow;
- docs for verifying final state on-chain.

Done when:
- the public testnet job can be finalized and funds can be withdrawn through the existing contract functions.

---

### Track 9. Public demo helper commands and scripts

Stage 6 introduced canonical local helper commands.
Stage 7 must do the same for the public path.

Recommended helper commands:
- `public-check-env`
- `public-deploy`
- `public-create-job`
- `public-fund-job`
- `public-sync-job`
- `public-start-flow`
- `public-submit-attestation`
- `public-finalize-job`
- `public-withdraw`
- `public-status`

Selected Stage 7 helper surface:
- Make targets wrap readable shell scripts under `infra/scripts/public-*.sh`
- on-chain writes remain explicit in helper scripts, not hidden inside orchestrator runtime

Tasks:
- decide whether the canonical entrypoint is Make, shell scripts, or both;
- keep helper scripts readable and explicit;
- document prerequisites and expected outputs.

Deliverables:
- canonical public-demo command sequence.

Done when:
- the public MVP can be run from a short, documented command path.

---

### Track 10. Observability and verification

A public-chain demo must be inspectable from both off-chain and on-chain surfaces.

Tasks:
- make it easy to inspect:
  - current network / chain ID
  - contract address
  - job state on-chain
  - job state off-chain
  - round state
  - attestation state
  - settlement state
  - task state
  - evaluation reports
  - relevant tx hashes
- document one verification checklist for presentations.

Recommended inspection surfaces:
- orchestrator `/health`
- orchestrator `/status`
- `/jobs`
- `/jobs/{id}`
- `/jobs/{id}/rounds`
- `/rounds/{id}`
- helper commands for contract state reads
- helper commands for tx / address / balance inspection

Deliverables:
- public-status inspection path;
- documented verification checklist.

Done when:
- a developer can explain what happened during a public demo without opening the database manually.

---

### Track 11. Public demo documentation

This is the most visible Stage 7 deliverable.

Tasks:
- add a public-demo setup guide;
- update README with Stage 7 summary and public quickstart;
- document:
  - prerequisites
  - wallet/key assumptions
  - deployment
  - job creation/funding
  - sync
  - run flow
  - attestation
  - finalization
  - withdrawal
  - verification
  - cleanup / reset expectations

Recommended docs:
- `docs/setup/public-demo.md`
- update `docs/setup/development.md`
- update `README.md`
- commit `docs/mvp/stage-7-plan.md`

Deliverables:
- public demo documentation that another developer can follow.

Done when:
- another developer can reproduce the public testnet demo from docs alone.

---

### Track 12. Public testnet verification path

Stage 6 had `demo-smoke` for local execution.
Stage 7 needs a verification path appropriate for public testnet integration.

Tasks:
- define one canonical verification path for public demo readiness;
- script as much as is reasonable;
- clearly document any manual prerequisites such as funded testnet accounts.

Public verification should cover:
- contract deployment succeeds;
- a job can be created and funded;
- the orchestrator syncs that job;
- the distributed training flow reaches `ready_for_attestation` or `evaluation_failed`;
- attestation can be submitted on-chain for the success path;
- finalization can be executed;
- payout/refund withdrawal can be verified.

Deliverables:
- one documented public verification path;
- expected outputs and checkpoints.

Done when:
- Stage 7 readiness can be checked without relying on tribal knowledge.

---

## File and module expectations

Stage 7 is expected to create or significantly expand files in these areas.

### Contracts / scripts
- public deployment scripts under `contracts/script/` or equivalent
- deployment artifact outputs under a documented path

### Infra
- `infra/env/*.env.example`
- `infra/scripts/public-*.sh`
- `Makefile`

### Orchestrator
- blockchain integration services as needed for public-chain sync and attestation/finalization wiring
- tests for public-chain-facing logic where realistic

### Docs
- `docs/mvp/stage-7-plan.md`
- `docs/codex/AGENTS-STAGE7-ADDENDUM.md`
- `docs/setup/public-demo.md`
- updates to `docs/setup/development.md`
- updates to `README.md`

---

## Recommended order of implementation

1. choose the canonical public testnet and freeze the Stage 7 scope;
2. harden public env/config;
3. add public deployment script and deployment artifact output;
4. add public job creation/funding helper flow;
5. verify orchestrator sync against public RPC;
6. run the existing distributed training flow against the synced public job;
7. integrate on-chain attestation submission;
8. integrate on-chain finalization and withdrawal helpers;
9. add public status/verification commands;
10. update docs and public runbook.

Do not start redesigning protocol internals or building UI before the public-chain flow is stable.

---

## Explicit non-goals for Stage 7

Do NOT implement in this stage:
- mainnet deployment;
- custom chain work;
- governance;
- token launch;
- trustless verification;
- malicious-node defense research;
- reputation/slashing;
- broader multi-protocol experimentation;
- UI.

These belong to later stages.

---

## Acceptance criteria

Stage 7 is complete only if all of the following are true:

1. one canonical public testnet path is defined;
2. the contract can be deployed to that network from repository instructions;
3. a public testnet job can be created and funded;
4. the orchestrator can sync that public on-chain job;
5. the existing distributed training flow reaches `ready_for_attestation` or `evaluation_failed` in the public setup;
6. for the success path, attestation can be submitted on-chain using the existing contract model;
7. the job can be finalized on-chain using the existing contract model;
8. payout/refund withdrawal can be executed and verified;
9. the full public demo is documented and inspectable;
10. Stage 7 does not widen into mainnet, UI, tokenomics, or trustless-verification work.

---

## Completion summary format

When Stage 7 is done, update this file with:

## Stage 7 implementation status
- Canonical public network: complete
- Public environment/config hardening: complete
- Public contract deployment path: complete
- Public job creation/funding flow: complete
- Public orchestrator sync: complete
- Public runtime flow for trainers/evaluator: complete
- On-chain attestation submission: complete
- On-chain finalization and withdrawals: complete
- Public helper commands/scripts: complete
- Observability and verification: complete
- Documentation: complete

## Delivered behavior
Stage 7 delivers the first public testnet demonstration of the distributed training marketplace: the contract is deployed to a canonical public EVM testnet, a funded job is created and synchronized into the orchestrator, the existing distributed training flow runs off-chain to a real post-evaluation outcome, and the existing contract model is used to submit attestation, finalize the job, and verify payout/refund behavior on-chain.
