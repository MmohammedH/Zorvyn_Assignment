from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from clients.db.connection import close_db, init_db
from clients.db.migrations import run_migrations
from config.config import get_settings
from handlers.error_handlers import setup_error_handlers
from log.logger import configure_logging, get_logger
from middleware.rate_limiter import limiter
from middleware.request_logging import RequestLoggingMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _startup()
    yield
    await _shutdown()


async def _startup() -> None:
    settings = get_settings()
    configure_logging(is_production=settings.is_production)
    logger.info(
        "Starting Finance System",
        extra={"version": settings.app_version, "env": settings.environment.value},
    )

    run_migrations()
    await init_db()
    await _seed_admin()

    logger.info("Finance System started successfully")


async def _shutdown() -> None:
    logger.info("Shutting down Finance System")
    await close_db()


async def _seed_admin() -> None:
    from clients.db.connection import AsyncSessionLocal
    from services.user_service import create_admin_seed, user_count

    settings = get_settings()
    async with AsyncSessionLocal() as session:
        count = await user_count(session)
        if count == 0:
            logger.info("No users found — seeding admin account")
            await create_admin_seed(
                session,
                email=settings.seed_admin_email,
                password=settings.seed_admin_password,
                full_name=settings.seed_admin_name,
            )
            await session.commit()
            logger.info(
                "Admin account seeded",
                extra={"email": settings.seed_admin_email},
            )


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Finance Dashboard Backend API",
        docs_url="/docs" if settings.is_dev else None,
        redoc_url="/redoc" if settings.is_dev else None,
        openapi_url="/openapi.json" if settings.is_dev else None,
        lifespan=lifespan,
        debug=settings.debug,
    )

    # Attach the limiter to the app so SlowAPIMiddleware can find it
    app.state.limiter = limiter

    _setup_middleware(app)
    setup_error_handlers(app)
    _setup_routes(app)

    return app


def _setup_middleware(app: FastAPI) -> None:
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=500)


def _setup_routes(app: FastAPI) -> None:
    from routes import auth, dashboard, financial_records, health, users

    prefix = "/api/v1"
    app.include_router(health.router)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(financial_records.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
