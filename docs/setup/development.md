# Development Setup

## Prerequisites
- Ubuntu-compatible shell environment
- Python 3.12
- Foundry (`forge`, `anvil`, `cast`)

## Bootstrap
```bash
make check-env
make bootstrap-dev
```

## Contract workflow
```bash
make contracts-build
make contracts-test
make contracts-fmt
```

## Python scaffold tests
```bash
make python-test
```

## Notes
- Stage 1 verifies the contract-local flow first.
- Off-chain services are intentionally placeholders; they are not yet wired into a runnable marketplace demo.
- Root environment defaults live in `.env.example`, while service-specific examples live under `infra/env/`.
