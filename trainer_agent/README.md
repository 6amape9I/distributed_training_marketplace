# Trainer Agent

Stage 3 turns the trainer agent into a real worker process.

## Responsibilities
- register with the orchestrator as a trainer node;
- send periodic heartbeats;
- claim `local_fit` tasks;
- execute local demo-grade training;
- upload result and report artifacts;
- expose `/health` and `/status`.

## Required configuration
- `TRAINER_NODE_ID`
- `ORCHESTRATOR_BASE_URL`
- `TRAINER_PUBLIC_URL`
- `LOCAL_WORKSPACE_PATH`

## Local run
```bash
PYTHONPATH=. .venv/bin/uvicorn trainer_agent.app.main:create_app --factory --host 0.0.0.0 --port 8010
```
