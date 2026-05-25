from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import get_session
from app.shared.auth.dependencies import require_roles
from app.identity.infrastructure.models import UserModel
from app.engagement.infrastructure.repositories import (
    SQLAlchemySubscriberRepository,
    SQLAlchemyArticleViewRepository,
)
from app.engagement.application.services import NewsletterService, AnalyticsService

# ── Newsletter router ─────────────────────────────────────────────────

newsletter_router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


class SubscribeRequest(BaseModel):
    email: EmailStr
    source: str = "website"


class UnsubscribeRequest(BaseModel):
    email: EmailStr


@newsletter_router.post("/subscribe", status_code=201)
async def subscribe(
    b: SubscribeRequest,
    db: AsyncSession = Depends(get_session),
):
    svc = NewsletterService(SQLAlchemySubscriberRepository(db))
    return await svc.subscribe(b.email, b.source)


@newsletter_router.post("/unsubscribe")
async def unsubscribe(
    b: UnsubscribeRequest,
    db: AsyncSession = Depends(get_session),
):
    svc = NewsletterService(SQLAlchemySubscriberRepository(db))
    result = await svc.unsubscribe(b.email)
    return {"message": "Unsubscribed successfully", **result}


@newsletter_router.get("/subscribers")
async def list_subscribers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    _u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    svc = NewsletterService(SQLAlchemySubscriberRepository(db))
    return await svc.list_subscribers(page=page, limit=limit, is_active=is_active)


@newsletter_router.get("/stats")
async def get_subscriber_stats(
    _u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    svc = NewsletterService(SQLAlchemySubscriberRepository(db))
    return await svc.get_stats()


# ── Analytics router ──────────────────────────────────────────────────

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_router.get("/overview")
async def get_overview(
    _u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    svc = AnalyticsService(SQLAlchemyArticleViewRepository(db))
    return await svc.get_overview()


@analytics_router.get("/pageviews")
async def get_pageviews(
    days: int = Query(30, ge=1, le=365),
    _u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    svc = AnalyticsService(SQLAlchemyArticleViewRepository(db))
    return await svc.get_pageviews(days=days)


@analytics_router.get("/traffic-sources")
async def get_traffic_sources(
    limit: int = Query(10, ge=1, le=50),
    _u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    svc = AnalyticsService(SQLAlchemyArticleViewRepository(db))
    return await svc.get_traffic_sources(limit=limit)


@analytics_router.get("/top-articles")
async def get_top_articles(
    limit: int = Query(10, ge=1, le=50),
    _u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    svc = AnalyticsService(SQLAlchemyArticleViewRepository(db))
    return await svc.get_top_articles(limit=limit)


@analytics_router.get("/reading-distribution")
async def get_reading_distribution(
    _u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    svc = AnalyticsService(SQLAlchemyArticleViewRepository(db))
    return await svc.get_reading_distribution()
