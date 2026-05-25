from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.engagement.infrastructure.models import (
    NewsletterSubscriberModel,
    ArticleViewModel,
)


class SQLAlchemySubscriberRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_dict(self, m: NewsletterSubscriberModel) -> dict:
        return {
            "id": str(m.id),
            "email": m.email,
            "is_active": m.is_active,
            "subscribed_at": m.subscribed_at,
            "unsubscribed_at": m.unsubscribed_at,
            "source": m.source,
        }

    async def get_by_email(self, email: str) -> dict | None:
        r = await self._session.execute(
            select(NewsletterSubscriberModel).where(
                NewsletterSubscriberModel.email == email
            )
        )
        m = r.scalar_one_or_none()
        return self._to_dict(m) if m else None

    async def create(self, data: dict) -> dict:
        m = NewsletterSubscriberModel(
            email=data["email"],
            is_active=data.get("is_active", True),
            subscribed_at=data.get("subscribed_at"),
            unsubscribed_at=data.get("unsubscribed_at"),
            source=data.get("source", "website"),
        )
        self._session.add(m)
        await self._session.flush()
        return self._to_dict(m)

    async def deactivate(self, subscriber_id: UUID) -> dict | None:
        r = await self._session.execute(
            select(NewsletterSubscriberModel).where(
                NewsletterSubscriberModel.id == subscriber_id
            )
        )
        m = r.scalar_one_or_none()
        if not m:
            return None
        m.is_active = False
        m.unsubscribed_at = datetime.now(timezone.utc).isoformat()
        await self._session.flush()
        return self._to_dict(m)

    async def list_subscribers(
        self,
        page: int = 1,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> tuple[list[dict], int]:
        q = select(NewsletterSubscriberModel)
        cq = select(func.count()).select_from(NewsletterSubscriberModel)

        if is_active is not None:
            q = q.where(NewsletterSubscriberModel.is_active == is_active)
            cq = cq.where(NewsletterSubscriberModel.is_active == is_active)

        q = q.order_by(NewsletterSubscriberModel.subscribed_at.desc())

        total = (await self._session.execute(cq)).scalar() or 0
        r = await self._session.execute(q.offset((page - 1) * limit).limit(limit))
        items = [self._to_dict(m) for m in r.scalars().all()]
        return items, total

    async def get_stats(self) -> dict:
        total = (
            await self._session.execute(
                select(func.count()).select_from(NewsletterSubscriberModel)
            )
        ).scalar() or 0

        active = (
            await self._session.execute(
                select(func.count()).select_from(NewsletterSubscriberModel).where(
                    NewsletterSubscriberModel.is_active == True
                )
            )
        ).scalar() or 0

        return {"total_subscribers": total, "active_subscribers": active}


class SQLAlchemyArticleViewRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def record_view(
        self,
        article_id: UUID,
        visitor_fingerprint: str,
        referrer: str = "",
        read_duration_sec: int = 0,
    ) -> dict:
        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(minutes=30)).isoformat()

        existing = await self._session.execute(
            select(ArticleViewModel).where(
                and_(
                    ArticleViewModel.article_id == article_id,
                    ArticleViewModel.visitor_fingerprint == visitor_fingerprint,
                    ArticleViewModel.viewed_at >= cutoff,
                )
            )
        )
        if existing.scalar_one_or_none():
            return {"deduplicated": True}

        m = ArticleViewModel(
            article_id=article_id,
            visitor_fingerprint=visitor_fingerprint,
            referrer=referrer,
            read_duration_sec=read_duration_sec,
            viewed_at=now.isoformat(),
        )
        self._session.add(m)
        await self._session.flush()
        return {
            "id": str(m.id),
            "article_id": str(m.article_id),
            "visitor_fingerprint": m.visitor_fingerprint,
            "referrer": m.referrer,
            "read_duration_sec": m.read_duration_sec,
            "viewed_at": m.viewed_at,
        }

    async def get_overview(self) -> dict:
        total_views = (
            await self._session.execute(
                select(func.count()).select_from(ArticleViewModel)
            )
        ).scalar() or 0

        unique_visitors = (
            await self._session.execute(
                select(
                    func.count(
                        func.distinct(ArticleViewModel.visitor_fingerprint)
                    )
                ).select_from(ArticleViewModel)
            )
        ).scalar() or 0

        avg_read = (
            await self._session.execute(
                select(func.avg(ArticleViewModel.read_duration_sec))
            )
        ).scalar() or 0

        return {
            "total_views": total_views,
            "unique_visitors": unique_visitors,
            "avg_read_duration_sec": round(float(avg_read), 1),
        }

    async def get_pageviews(self, days: int = 30) -> list[dict]:
        from sqlalchemy import text

        r = await self._session.execute(
            text(
                """
                SELECT DATE(viewed_at) AS date, COUNT(*) AS views
                FROM article_views
                WHERE viewed_at >= (NOW() - INTERVAL :days DAY)::text
                GROUP BY DATE(viewed_at)
                ORDER BY date DESC
                """
            ),
            {"days": days},
        )
        return [{"date": str(row[0]), "views": row[1]} for row in r.fetchall()]

    async def get_traffic_sources(self, limit: int = 10) -> list[dict]:
        r = await self._session.execute(
            select(ArticleViewModel.referrer, func.count().label("count"))
            .group_by(ArticleViewModel.referrer)
            .order_by(desc("count"))
            .limit(limit)
        )
        return [{"referrer": row[0] or "direct", "count": row[1]} for row in r.fetchall()]

    async def get_top_articles(self, limit: int = 10) -> list[dict]:
        r = await self._session.execute(
            select(
                ArticleViewModel.article_id,
                func.count().label("views"),
                func.avg(ArticleViewModel.read_duration_sec).label("avg_duration"),
            )
            .group_by(ArticleViewModel.article_id)
            .order_by(desc("views"))
            .limit(limit)
        )
        return [
            {
                "article_id": str(row[0]),
                "views": row[1],
                "avg_read_duration_sec": round(float(row[2] or 0), 1),
            }
            for row in r.fetchall()
        ]

    async def get_reading_distribution(self) -> list[dict]:
        r = await self._session.execute(
            select(
                func.case(
                    (
                        ArticleViewModel.read_duration_sec < 10,
                        "0-10s",
                    ),
                    (
                        ArticleViewModel.read_duration_sec < 30,
                        "10-30s",
                    ),
                    (
                        ArticleViewModel.read_duration_sec < 60,
                        "30-60s",
                    ),
                    (
                        ArticleViewModel.read_duration_sec < 180,
                        "1-3min",
                    ),
                    else_="3min+",
                ).label("bucket"),
                func.count().label("count"),
            ).group_by("bucket")
        )
        return [{"bucket": row[0], "count": row[1]} for row in r.fetchall()]
