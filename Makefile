VENV ?= .venv/bin
PYTHON ?= $(VENV)/python
PYTEST ?= $(VENV)/pytest

.PHONY: check-env bootstrap-dev contracts-build contracts-test contracts-fmt python-test db-migrate orchestrator-run

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
	PYTHONPATH=. $(PYTEST) orchestrator/app/tests trainer_agent/app/tests

db-migrate:
	PYTHONPATH=. $(VENV)/alembic -c orchestrator/alembic.ini upgrade head

orchestrator-run:
	PYTHONPATH=. $(VENV)/uvicorn orchestrator.app.api.main:create_app --factory --host 0.0.0.0 --port 8000
