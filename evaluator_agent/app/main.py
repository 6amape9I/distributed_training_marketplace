from fastapi import FastAPI

from evaluator_agent.app.settings import EvaluatorSettings


def create_app() -> FastAPI:
    settings = EvaluatorSettings()
    app = FastAPI(title=settings.service_name, version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

    return app


app = create_app()
