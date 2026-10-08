import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from cafesito import __version__
from cafesito.api.errors import register_error_handlers
from cafesito.api.routers import analytics, health, predictions, recommendations, segments
from cafesito.config import Settings, get_settings
from cafesito.db.session import create_db_engine, create_session_factory
from cafesito.ml.artifacts import load_artifacts

WEB_DIR = Path(__file__).resolve().parents[1] / "web"
logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(settings.database_url)
        app.state.session_factory = create_session_factory(engine)
        app.state.model_store = load_artifacts(settings.models_dir)
        logger.info("Application ready")
        yield
        engine.dispose()

    app = FastAPI(
        title="Cafesito Feli API",
        version=__version__,
        description="Sales analytics and machine learning services for Cafesito Feli.",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    register_error_handlers(app)
    for router in (
        health.router,
        analytics.router,
        predictions.router,
        segments.router,
        recommendations.router,
    ):
        app.include_router(router, prefix="/api")
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
