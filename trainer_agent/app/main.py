from fastapi import FastAPI

from trainer_agent.app.settings import TrainerSettings


def create_app() -> FastAPI:
    settings = TrainerSettings()
    app = FastAPI(title=settings.service_name, version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

    return app


app = create_app()
