from uuid import UUID
from datetime import datetime, timezone

from app.engagement.infrastructure.repositories import (
    SQLAlchemySubscriberRepository,
    SQLAlchemyArticleViewRepository,
)
from app.engagement.domain import events as domain_events
from app.shared.events.event_bus import event_bus
from app.shared.exceptions import ConflictError, NotFoundError
from app.shared.pagination import paginate


class NewsletterService:
    def __init__(self, repo: SQLAlchemySubscriberRepository):
        self._repo = repo

    async def subscribe(self, email: str, source: str = "website") -> dict:
        existing = await self._repo.get_by_email(email)
        if existing:
            if existing["is_active"]:
                raise ConflictError("Email is already subscribed")
            now = datetime.now(timezone.utc).isoformat()
            from app.engagement.infrastructure.models import NewsletterSubscriberModel
            from sqlalchemy import select
            r = await self._repo._session.execute(
                select(NewsletterSubscriberModel).where(
                    NewsletterSubscriberModel.email == email
                )
            )
            m = r.scalar_one_or_none()
            if m:
                m.is_active = True
                m.subscribed_at = now
                m.unsubscribed_at = None
                m.source = source
                await self._repo._session.flush()
            result = await self._repo.get_by_email(email)
            await event_bus.publish(
                domain_events.newsletter_subscribed(str(result["id"]), email, source)
            )
            return result

        now = datetime.now(timezone.utc).isoformat()
        data = {
            "email": email,
            "is_active": True,
            "subscribed_at": now,
            "source": source,
        }
        result = await self._repo.create(data)
        await event_bus.publish(
            domain_events.newsletter_subscribed(str(result["id"]), email, source)
        )
        return result

    async def unsubscribe(self, email: str) -> dict:
        existing = await self._repo.get_by_email(email)
        if not existing:
            raise NotFoundError("Subscriber not found")
        if not existing["is_active"]:
            return existing
        result = await self._repo.deactivate(UUID(existing["id"]))
        if result:
            await event_bus.publish(
                domain_events.newsletter_unsubscribed(result["id"], email)
            )
        return result or existing

    async def list_subscribers(
        self,
        page: int = 1,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> dict:
        items, total = await self._repo.list_subscribers(
            page=page, limit=min(limit, 100), is_active=is_active
        )
        return paginate(items, total, page, min(limit, 100))

    async def get_stats(self) -> dict:
        return await self._repo.get_stats()


class AnalyticsService:
    def __init__(self, repo: SQLAlchemyArticleViewRepository):
        self._repo = repo

    async def get_overview(self) -> dict:
        return await self._repo.get_overview()

    async def get_pageviews(self, days: int = 30) -> list[dict]:
        return await self._repo.get_pageviews(days=days)

    async def get_traffic_sources(self, limit: int = 10) -> list[dict]:
        return await self._repo.get_traffic_sources(limit=limit)

    async def get_top_articles(self, limit: int = 10) -> list[dict]:
        return await self._repo.get_top_articles(limit=limit)

    async def get_reading_distribution(self) -> list[dict]:
        return await self._repo.get_reading_distribution()
