VENV ?= .venv/bin
PYTHON ?= $(VENV)/python
PYTEST ?= $(VENV)/pytest

.PHONY: check-env bootstrap-dev contracts-build contracts-test contracts-fmt python-test db-migrate orchestrator-run demo-up demo-init demo-start-flow demo-status demo-logs demo-down demo-clean demo-smoke public-check-env public-deploy public-create-job public-fund-job public-sync-job public-start-flow public-submit-attestation public-finalize-job public-withdraw public-status

check-env:
	bash infra/scripts/check-env.sh

bootstrap-dev:
	bash infra/scripts/bootstrap-dev.sh

contracts-build:
	cd contracts && forge build

contracts-test:
	cd contracts && forge test

contracts-fmt:
	cd contracts && forge fmt

python-test:
	PYTHONPATH=. $(PYTEST) orchestrator/app/tests trainer_agent/app/tests evaluator_agent/app/tests shared/python/tests

db-migrate:
	PYTHONPATH=. $(VENV)/alembic -c orchestrator/alembic.ini upgrade head

orchestrator-run:
	PYTHONPATH=. $(VENV)/uvicorn orchestrator.app.api.main:create_app --factory --host 0.0.0.0 --port 8000

demo-up:
	bash infra/scripts/demo-up.sh

demo-init:
	bash infra/scripts/demo-init.sh

demo-start-flow:
	bash infra/scripts/demo-start-flow.sh

demo-status:
	bash infra/scripts/demo-status.sh

demo-logs:
	bash infra/scripts/demo-logs.sh

demo-down:
	bash infra/scripts/demo-down.sh

demo-clean:
	bash infra/scripts/demo-clean.sh

demo-smoke:
	bash infra/scripts/demo-smoke.sh

public-check-env:
	bash infra/scripts/public-check-env.sh

public-deploy:
	bash infra/scripts/public-deploy.sh

public-create-job:
	bash infra/scripts/public-create-job.sh

public-fund-job:
	bash infra/scripts/public-fund-job.sh

public-sync-job:
	bash infra/scripts/public-sync-job.sh

public-start-flow:
	bash infra/scripts/public-start-flow.sh

public-submit-attestation:
	bash infra/scripts/public-submit-attestation.sh

public-finalize-job:
	bash infra/scripts/public-finalize-job.sh

public-withdraw:
	bash infra/scripts/public-withdraw.sh

public-status:
	bash infra/scripts/public-status.sh
