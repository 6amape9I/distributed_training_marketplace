# Repository Structure and Stage 1 Plan

## 1. Target repository structure

```text
.
├── .codexignore
├── .env.example
├── .gitignore
├── AGENTS.md
├── README.md
├── Makefile
├── pyproject.toml
├── requirements-dev.txt
├── docs/
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── domain-model.md
│   │   └── adr/
│   │       └── 0001-onchain-offchain-boundary.md
│   ├── mvp/
│   │   ├── scope.md
│   │   ├── stage-1-plan.md
│   │   └── acceptance-criteria.md
│   ├── setup/
│   │   ├── development.md
│   │   └── local-demo.md
│   └── codex/
│       ├── PROJECT_BRIEF_FOR_CODEX.md
│       └── AGENTS-CODEX-ADDENDUM.md
├── contracts/
│   ├── foundry.toml
│   ├── remappings.txt
│   ├── src/
│   │   ├── TrainingMarketplace.sol
│   │   ├── interfaces/
│   │   │   └── ITrainingMarketplace.sol
│   │   ├── libraries/
│   │   ├── types/
│   │   └── errors/
│   ├── script/
│   │   └── DeployLocal.s.sol
│   ├── test/
│   │   ├── TrainingMarketplace.t.sol
│   │   ├── JobLifecycle.t.sol
│   │   └── Settlement.t.sol
│   └── README.md
├── orchestrator/
│   ├── app/
│   │   ├── api/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   │   ├── health.py
│   │   │   │   ├── jobs.py
│   │   │   │   └── nodes.py
│   │   │   └── deps.py
│   │   ├── application/
│   │   │   ├── services/
│   │   │   ├── protocols/
│   │   │   │   ├── training_protocol.py
│   │   │   │   ├── aggregation_strategy.py
│   │   │   │   ├── evaluation_strategy.py
│   │   │   │   ├── artifact_repository.py
│   │   │   │   ├── node_selection_strategy.py
│   │   │   │   └── payout_policy.py
│   │   │   └── dto/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   ├── enums/
│   │   │   ├── value_objects/
│   │   │   └── repositories/
│   │   ├── infrastructure/
│   │   │   ├── blockchain/
│   │   │   ├── db/
│   │   │   ├── storage/
│   │   │   └── settings/
│   │   └── tests/
│   └── README.md
├── trainer_agent/
│   ├── app/
│   │   ├── main.py
│   │   ├── training/
│   │   ├── transport/
│   │   └── settings.py
│   └── README.md
├── evaluator_agent/
│   ├── app/
│   │   ├── main.py
│   │   ├── evaluation/
│   │   ├── transport/
│   │   └── settings.py
│   └── README.md
├── shared/
│   ├── python/
│   │   ├── schemas/
│   │   ├── enums/
│   │   ├── hashing/
│   │   └── ids/
│   └── README.md
└── infra/
    ├── compose/
    │   ├── compose.dev.yml
    │   └── compose.demo.yml
    ├── env/
    │   ├── orchestrator.env.example
    │   ├── trainer.env.example
    │   └── evaluator.env.example
    ├── docker/
    │   ├── orchestrator.Dockerfile
    │   ├── trainer.Dockerfile
    │   └── evaluator.Dockerfile
    └── scripts/
        ├── bootstrap-dev.sh
        ├── run-local-stack.sh
        └── check-env.sh
```

## 2. Files that must be created immediately

These files should exist at repository bootstrap, even if some are placeholders at first:

### Root
- `.gitignore`
- `.codexignore`
- `.env.example`
- `README.md`
- `AGENTS.md`
- `Makefile`
- `pyproject.toml`
- `requirements-dev.txt`

### Documentation
- `docs/architecture/overview.md`
- `docs/architecture/domain-model.md`
- `docs/architecture/adr/0001-onchain-offchain-boundary.md`
- `docs/mvp/scope.md`
- `docs/mvp/stage-1-plan.md`
- `docs/mvp/acceptance-criteria.md`
- `docs/setup/development.md`
- `docs/setup/local-demo.md`
- `docs/codex/PROJECT_BRIEF_FOR_CODEX.md`
- `docs/codex/AGENTS-CODEX-ADDENDUM.md`

### Contracts bootstrap
- `contracts/foundry.toml`
- `contracts/src/TrainingMarketplace.sol`
- `contracts/test/TrainingMarketplace.t.sol`
- `contracts/script/DeployLocal.s.sol`
- `contracts/README.md`

### Orchestrator bootstrap
- `orchestrator/app/api/main.py`
- `orchestrator/app/application/protocols/training_protocol.py`
- `orchestrator/app/application/protocols/aggregation_strategy.py`
- `orchestrator/app/application/protocols/evaluation_strategy.py`
- `orchestrator/app/application/protocols/artifact_repository.py`
- `orchestrator/app/application/protocols/node_selection_strategy.py`
- `orchestrator/app/application/protocols/payout_policy.py`
- `orchestrator/README.md`

### Agents bootstrap
- `trainer_agent/app/main.py`
- `trainer_agent/README.md`
- `evaluator_agent/app/main.py`
- `evaluator_agent/README.md`

### Infra bootstrap
- `infra/compose/compose.dev.yml`
- `infra/scripts/check-env.sh`
- `infra/scripts/bootstrap-dev.sh`
- `infra/scripts/run-local-stack.sh`

## 3. Stage 1 goal

**Stage 1 = Smart contract trust layer + repository bootstrap**

At the end of Stage 1 we must have:
- a clean repository skeleton;
- baseline docs;
- Foundry-based contract workspace;
- a tested contract implementing generic job lifecycle + escrow + attestation + settlement;
- no dependency on FL-specific contract concepts.

## 4. Stage 1 task list

### Track A — Repository bootstrap
1. Initialize repository skeleton according to the target structure.
2. Add root metadata files (`README.md`, `.gitignore`, `.env.example`, `Makefile`).
3. Add `pyproject.toml` and `requirements-dev.txt` for Python tooling bootstrap.
4. Copy the Codex guidance docs into `docs/codex/`.
5. Create minimal `AGENTS.md` and include the Codex addendum reference.

### Track B — Architecture documentation
6. Write `docs/architecture/overview.md` explaining on-chain/off-chain split.
7. Write `docs/architecture/domain-model.md` with the generic domain entities:
   - Job
   - Round
   - Contribution/Submission
   - Evaluation
   - Settlement
8. Write ADR `0001-onchain-offchain-boundary.md` stating that heavy ML logic stays off-chain.
9. Write `docs/mvp/scope.md` describing what MVP includes and excludes.
10. Write `docs/mvp/acceptance-criteria.md` for Stage 1.

### Track C — Foundry workspace initialization
11. Initialize the `contracts/` subproject as a proper Foundry workspace.
12. Add OpenZeppelin dependency.
13. Configure `foundry.toml` and remappings cleanly.
14. Add `contracts/README.md` with local commands for build/test/anvil/deploy.

### Track D — Contract domain design
15. Design a generic contract API around:
   - creating a job;
   - funding escrow;
   - attesting result/round data;
   - finalizing a job;
   - payout/refund.
16. Define events for every major lifecycle transition.
17. Define access-control rules.
18. Keep the ABI generic and future-proof: no FL-specific naming.

### Track E — Contract implementation
19. Implement `TrainingMarketplace.sol`.
20. Use OpenZeppelin primitives where appropriate.
21. Introduce custom errors for invalid transitions and unauthorized calls.
22. Implement the job lifecycle state machine.
23. Implement escrow accounting.
24. Implement finalization logic.
25. Implement payout/refund logic.

### Track F — Contract tests
26. Add happy-path tests for:
   - job creation;
   - funding;
   - attestation;
   - finalization;
   - payout;
   - refund.
27. Add failure-path tests for:
   - unauthorized actions;
   - invalid status transitions;
   - double finalization;
   - insufficient funds;
   - payout/refund edge cases.
28. Ensure `forge test` passes cleanly.

### Track G — Local scripts and smoke flow
29. Add `DeployLocal.s.sol`.
30. Add `infra/scripts/check-env.sh`.
31. Add a minimal `run-local-stack.sh` that starts Anvil and documents the expected local sequence.
32. Document the Stage 1 local smoke path in `docs/setup/development.md`.

### Track H — Off-chain placeholders for future stages
33. Create orchestrator protocol interface files as empty-but-typed scaffolding.
34. Add `trainer_agent/app/main.py` and `evaluator_agent/app/main.py` placeholders.
35. Do not implement real training logic yet; just create the extension points.

## 5. Stage 1 acceptance criteria

Stage 1 is complete only if all conditions below are true:

1. The repository structure is in place and readable.
2. The architecture docs clearly describe the on-chain/off-chain boundary.
3. The contract workspace builds successfully with Foundry.
4. All contract tests pass.
5. A local deploy script exists and works against Anvil.
6. The contract models a generic marketplace lifecycle rather than an FL-specific one.
7. Placeholder extension points exist for future off-chain protocol work.
8. A new contributor can understand how the repository is organized and what Stage 2 will build on top of Stage 1.

## 6. Important implementation notes for Codex

- The first protocol may be FedAvg-like later, but **nothing in Stage 1 contracts should imply that forever**.
- Avoid introducing `trainer`/`validator` assumptions directly into the contract data model unless they are truly generic roles for the marketplace lifecycle.
- Keep business logic small and explicit.
- If a naming choice feels “too MVP-specific”, rename it now before code spreads.
