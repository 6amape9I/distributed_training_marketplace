# Repository Guidelines

## Project Structure & Module Organization
This repository implements Stage 1 of a distributed training marketplace. Keep blockchain trust logic in `contracts/` and off-chain execution scaffolding in `orchestrator/`, `trainer_agent/`, `evaluator_agent/`, and `shared/`. Use `docs/` for architecture and setup notes; `infra/` holds compose files, Dockerfiles, and helper scripts.

## Build, Test, and Development Commands
- `make check-env`: verify Foundry and Python prerequisites.
- `make contracts-build`: compile the canonical Foundry workspace in `contracts/`.
- `make contracts-test`: run contract unit tests.
- `make contracts-fmt`: format Solidity sources.
- `make python-test`: run scaffold smoke tests for the orchestrator.

## Coding Style & Naming Conventions
Use 4-space indentation in Python and `forge fmt` for Solidity. Keep Python transport, domain, and application layers separate. Use `snake_case` for Python modules, `PascalCase` for classes, and generic contract/domain names such as `Job`, `Attestation`, and `Settlement` instead of FL-specific terms.

## Testing Guidelines
Contract tests live in `contracts/test/` and must cover lifecycle transitions, authorization, and settlement edge cases. Python tests live in `orchestrator/app/tests/` and should validate importability plus basic API behavior.

## Commit & Pull Request Guidelines
Use scoped commit messages such as `feat(contracts): add job settlement flow` or `docs(architecture): define on-chain boundary`. Pull requests should include a short description, linked task, test evidence, and documentation updates when architecture or workflow changes.

## Agent-Specific Instructions
Read `docs/codex/AGENTS-CODEX-ADDENDUM.md` before structural changes. Preserve the on-chain/off-chain boundary and keep ML execution logic out of smart contracts.
