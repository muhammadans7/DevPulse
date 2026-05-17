from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.constants.api import (
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

    return app


app = create_app()
