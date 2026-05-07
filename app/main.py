from fastapi import FastAPI

from app.api.chat import router as chat_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="RepoPilot",
        description="Agentic CodeOps API for repository analysis workflows.",
        version="0.1.0",
    )
    app.include_router(chat_router)
    return app


app = create_app()
