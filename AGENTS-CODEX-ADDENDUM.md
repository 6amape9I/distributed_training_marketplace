# AGENTS Addendum for Codex

This document supplements `AGENTS.md` and defines how Codex should work in this repository.

## 1. General working mode
Codex must behave as an implementation agent for a serious engineering project, not as a code generator for quick hacks.

Primary priorities, in order:
1. preserve architectural boundaries;
2. keep the MVP path short;
3. avoid decisions that lock the project into one protocol forever;
4. leave a readable trail in code, docs, and commits.

## 2. Architectural discipline
Codex must preserve the separation between:
- **on-chain trust/settlement**;
- **off-chain execution**.

### Strict rule
Never place ML execution logic into smart contracts.
Never model blockchain contracts around FL-only concepts such as “gradient tensor” or “federated delta”.
Contracts should speak in generic domain terms:
- Job;
- Round;
- Submission/Attestation;
- Evaluation;
- Settlement.

## 3. MVP discipline
Codex is allowed to implement a **FedAvg-like protocol for the first runnable path**, but must not hardcode the whole codebase around FedAvg.

Mandatory extension points:
- `TrainingProtocol`
- `AggregationStrategy`
- `EvaluationStrategy`
- `NodeSelectionStrategy`
- `ArtifactRepository`
- `PayoutPolicy`

If a fast implementation needs a default concrete class, use a clearly named default such as:
- `FedAvgTrainingProtocol`
- `SimpleWeightedAverageAggregation`
- `LocalFilesystemArtifactRepository`

## 4. Repository hygiene
Codex must:
- prefer small, reviewable commits;
- keep docs synchronized with code;
- avoid introducing dead files, generated noise, or duplicated examples;
- not edit dependency/vendor directories unless explicitly required.

## 5. Documentation rules
Whenever Codex introduces a non-obvious architectural decision, it must update or create the relevant document in `docs/`.

At minimum:
- update `docs/architecture/overview.md` if boundaries or module responsibilities change;
- update `docs/mvp/stage-1-plan.md` when tasks are completed or re-scoped;
- add an ADR when a decision meaningfully affects future extensibility.

## 6. Coding rules
### Python
- Use type hints in all application-facing code.
- Prefer Pydantic models for external payloads.
- Keep domain logic separate from transport code.
- Do not mix REST controller logic with orchestration core.
- Use explicit interfaces / protocols / abstract base classes where extension is expected.

### Solidity
- Keep contracts minimal and domain-focused.
- Emit events for all important lifecycle transitions.
- Prefer custom errors where appropriate.
- Use OpenZeppelin battle-tested components instead of handwritten access control or ownership code.
- Write tests for all state transitions and failure paths.

## 7. Testing rules
Codex must not leave core logic untested.

Minimum expectations:
- contract unit tests for creation, attestation, finalization, payout, refund, and authorization;
- Python tests for pure domain/application logic where practical;
- one smoke path for the contract-local workflow.

## 8. Handling shortcuts
If Codex uses an MVP shortcut, it must document it explicitly in code comments or docs.
Examples of acceptable shortcuts:
- local filesystem instead of S3;
- SQLite instead of PostgreSQL;
- single evaluator implementation;
- static node assignment instead of sophisticated scheduling.

Examples of unacceptable shortcuts:
- hardcoding the entire system to FedAvg forever;
- storing heavy model payloads on-chain;
- mixing orchestration logic into API handlers;
- using undocumented magic constants across modules.

## 9. What Codex should avoid
Avoid:
- premature microservices fragmentation;
- premature event buses or queues if direct orchestration is sufficient;
- tokenomics work;
- frontend work;
- security theater instead of clear MVP boundaries;
- generated boilerplate without purpose.

## 10. Definition of “done” for a task
A task is not done until:
- code is added;
- tests are added or updated where required;
- docs are updated if the behavior or architecture changed;
- configuration and run instructions remain coherent.

## 11. Communication style in commits and PRs
Codex should use clear, boring, technical language.
Good examples:
- `feat(contracts): add job lifecycle and settlement events`
- `feat(orchestrator): introduce training protocol interface`
- `test(contracts): cover payout and refund flows`
- `docs(architecture): document on-chain/off-chain boundary`

## 12. Preferred implementation sequence
Codex should follow the staged plan from `docs/mvp/stage-1-plan.md` and should not jump deep into trainer/evaluator implementation before the repository skeleton and trust layer are in place.
