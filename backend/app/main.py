"""
Personal AI Presentation — FastAPI Backend Entry Point (Phase 3 Step 3)
Multi-tenant SaaS: JWT auth, DB, async tasks, rate-limiter, privacy shredder, prompt shield.

Start with:
    uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.models.slide import HealthResponse
from app.routes import generate, export, auth, payment
from app.services.purge_scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # ═══ Startup ═══
    logger.info(f"Starting {settings.APP_NAME} v0.3.1")
    logger.info(f"LLM Provider: {settings.LLM_API_BASE}")
    logger.info(f"LLM Model: {settings.LLM_MODEL_NAME}")
    logger.info(f"Image Provider: {settings.IMAGE_PROVIDER}")
    logger.info(f"Database: {settings.DATABASE_URL.split('://')[0]}")

    if not settings.LLM_API_KEY:
        logger.warning("LLM_API_KEY not set — generation features will fail!")

    # Database auto-init
    await init_db()
    logger.info("Database initialized")

    # Layout plugin registry auto-discovery
    from app.layouts.registry import layout_registry
    layout_registry.auto_discover()
    logger.info(
        f"Layout registry loaded — {len(layout_registry.get_names('premium'))} layout plugins "
        f"(free={len(layout_registry.get_names('free'))}, "
        f"premium={len(layout_registry.get_names('premium'))})"
    )

    # Privacy shredder (APScheduler — hourly cron)
    start_scheduler()

    yield

    # ═══ Shutdown ═══
    stop_scheduler()
    logger.info(f"{settings.APP_NAME} shut down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.3.1",
        description=(
            "Multi-tenant SaaS AI presentation platform. "
            "JWT authentication, async task queue, rate-limited, "
            "multi-provider LLM, multi-language, image pipeline, "
            "privacy shredder (APScheduler), prompt injection shield."
        ),
        docs_url="/docs" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(generate.router)
    app.include_router(export.router)
    app.include_router(payment.router)

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        return HealthResponse(
            status="ok",
            version="0.3.1",
            llm_provider=settings.LLM_API_BASE.split("//")[1].split("/")[0]
            if "//" in settings.LLM_API_BASE
            else "unknown",
        )

    return app


app = create_app()
