from contextlib import asynccontextmanager
import time
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.shared.exceptions import AppException, app_exception_handler, validation_exception_handler

logger = logging.getLogger(__name__)
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import app.identity.event_handlers
    import app.administration.event_handlers
    logger.info("PyFlow Blog API starting up")
    yield
    logger.info("PyFlow Blog API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="PyFlow Blog API",
        description="Backend API for the PyFlow blog platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    from app.identity.api.router import router as auth_router, users_router
    from app.content.api.router import router as articles_router, categories_router, tags_router, search_router
    from app.media.api.router import router as media_router
    from app.engagement.api.router import newsletter_router, analytics_router
    from app.intelligence.api.router import router as ai_router
    from app.administration.api.router import settings_router, activity_log_router, health_router

    prefix = settings.API_PREFIX
    app.include_router(auth_router, prefix=prefix)
    app.include_router(users_router, prefix=prefix)
    app.include_router(articles_router, prefix=prefix)
    app.include_router(categories_router, prefix=prefix)
    app.include_router(tags_router, prefix=prefix)
    app.include_router(search_router, prefix=prefix)
    app.include_router(media_router, prefix=prefix)
    app.include_router(newsletter_router, prefix=prefix)
    app.include_router(analytics_router, prefix=prefix)
    app.include_router(ai_router, prefix=prefix)
    app.include_router(settings_router, prefix=prefix)
    app.include_router(activity_log_router, prefix=prefix)
    app.include_router(health_router, prefix=prefix)

    return app


app = create_app()
