# AGENTS Stage 7 Addendum

## Purpose of Stage 7

Stage 7 is about public-chain integration credibility.

The goal is not to invent a new protocol.
The goal is not to redesign the contract layer.
The goal is not to build production infrastructure.

The goal is to prove that the marketplace can leave the local demo environment and operate against a real public testnet trust layer.

A good Stage 7 gives us:
- one obvious public network target,
- one obvious way to deploy,
- one obvious way to create and fund a public job,
- one obvious way to run the off-chain training flow against that job,
- one obvious way to submit attestation and finalize on-chain,
- one obvious way to verify the result.

---

## What must remain true

1. Do not redesign the Stage 1 smart-contract model unless a real blocker is proven.
2. Keep all model execution, aggregation, and evaluation off-chain.
3. Reuse the Stage 5 protocol plugin and the Stage 6 demo flow as much as possible.
4. Stage 7 is integration work, not research expansion.
5. Prefer one canonical public testnet path over many partially maintained network variants.
6. Public scripts and docs must be explicit enough that another developer can reproduce the demo.

---

## Stage 7 is successful only if

- the contract is deployed to a public testnet from repository instructions;
- a funded job can be created on that network;
- the orchestrator can synchronize real public-chain state;
- the distributed training flow still reaches a real pre-attestation outcome;
- attestation can be submitted on-chain;
- the job can be finalized on-chain;
- payout/refund behavior can be demonstrated clearly.

If the repository still proves only a local Anvil flow, Stage 7 is not complete.

---

## What not to do

Do not:
- turn Stage 7 into mainnet readiness work;
- add UI or wallet-product flows;
- redesign the protocol because public integration exposed operational inconvenience;
- widen the stage into trustless verification, slashing, or adversarial-node research;
- introduce custom chain work;
- create a large multi-network matrix before one canonical path is stable;
- hide critical public-demo logic in opaque scripts without documentation.

If implementation drifts into mainnet launch, tokenomics, or production platform work, it has left Stage 7.

---

## Architecture rules

### 1. Public integration must wrap the existing architecture, not replace it
The Stage 5/6 flow already proved:
- orchestrator
- trainer agents
- evaluator agent
- off-chain rounds
- aggregation
- evaluation
- lifecycle progression

Stage 7 must connect that flow to a public trust layer.
It must not replace the architecture with a separate one-off public demo implementation.

### 2. Keep the contract boundary generic
The contract does not need to learn about gradients, tensor formats, or protocol internals.
Use the existing generic job / attestation / settlement model.

### 3. Attestation and settlement must be explicit
Do not bury critical on-chain writes deep inside hidden automation.
The public demo must make it clear:
- when attestation is submitted,
- what hash is being submitted,
- when finalization happens,
- what payout/refund values are used.

### 4. One canonical public path is better than several incomplete variants
If choosing between:
- one well-documented public testnet flow, and
- several partly working testnet options,

choose the one well-documented flow.

### 5. Docs and helper commands are part of the feature
If the public demo requires chat-history memory or tribal knowledge, treat the implementation as incomplete.

---

## Preferred implementation bias

When choosing between:
- a smaller but real public testnet flow, and
- a broader but fragile “network support” story,

choose the smaller real flow.

Examples:
- better: one canonical public testnet with clear commands
- worse: three networks with inconsistent scripts

- better: explicit attestation and finalization helper steps
- worse: hidden on-chain writes buried in runtime side effects

- better: one documented success-path demo
- worse: many loosely described edge-case flows

- better: deterministic, documented demo values for settlement
- worse: vague payout logic that no one can explain during a presentation

---

## Required implementation style

- Keep helper scripts readable and explicit.
- Keep docs aligned with actual commands.
- Make network, chain ID, contract address, and account roles visible.
- Fail early on missing RPC or missing keys.
- Preserve inspectability:
  - chain context
  - contract address
  - job state
  - rounds
  - trainer tasks
  - evaluation tasks
  - attestation state
  - settlement state
  - tx hashes
- Keep public secrets out of committed code.

---

## Required testing and verification focus

Verification must prove:
- deployment works on the canonical public testnet;
- a real funded job can be created;
- the orchestrator can see and use that job;
- the off-chain training flow still works;
- the success path reaches on-chain attestation and finalization;
- payout/refund withdrawal can be demonstrated.

Do not treat “deployment succeeded” as proof that Stage 7 is complete.

---

## Required delivery discipline

When committing Stage 7 work:
- keep public-network config changes scoped and documented;
- update docs together with scripts;
- document all wallet/account assumptions for the demo;
- document what remains manual;
- preserve the local Stage 6 path rather than breaking it;
- make it clear which commands are canonical for local demo and which are canonical for public demo.

If a new public script becomes the preferred path, the docs must say so clearly.

---

## Escalation rule

If Stage 7 appears to require:
- redesigning the Stage 1 contract model,
- changing the protocol architecture,
- building a wallet UI,
- introducing mainnet infrastructure,
- adding trustless verification,
- redesigning payout economics,
- major trainer/evaluator rewrites,

stop and document the blocker before proceeding.

Do not quietly widen the stage.

---

## Final reminder

Stage 7 is the first proof that this is not just a local lab stand.

A good Stage 7 lets someone:
- deploy the contract to the canonical public testnet,
- create and fund a real public job,
- sync that job into the orchestrator,
- run the existing distributed training flow,
- submit attestation and finalize on-chain,
- verify the result from both off-chain and on-chain surfaces.

That is enough.