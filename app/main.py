from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.router import router as v1_router
from app.constants.api import (
    API_V1_PREFIX,
    DOCS_URL,
    OPENAPI_URL,
    PROJECT_DESCRIPTION,
    PROJECT_TITLE,
    PROJECT_VERSION,
    REDOC_URL,
)
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events — replaces Django's AppConfig.ready()."""
    await init_db()
    yield


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application instance."""
    app = FastAPI(
        title=PROJECT_TITLE,
        description=PROJECT_DESCRIPTION,
        version=PROJECT_VERSION,
        docs_url=DOCS_URL,
        redoc_url=REDOC_URL,
        openapi_url=OPENAPI_URL,
        lifespan=lifespan,
    )
    app.include_router(v1_router, prefix=API_V1_PREFIX)
    return app


app = create_app()
