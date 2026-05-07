from fastapi import FastAPI

from app.api.chat import router as chat_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="RepoPilot",
        description="面向仓库分析工作流的 Agentic CodeOps API。",
        version="0.1.0",
    )
    app.include_router(chat_router)
    return app


app = create_app()
