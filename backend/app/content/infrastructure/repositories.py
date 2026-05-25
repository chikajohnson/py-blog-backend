from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.content.domain.entities import Article, Category, Tag, ArticleStatus
from app.content.domain.repositories import ArticleRepository, CategoryRepository, TagRepository
from app.content.infrastructure.models import ArticleModel, CategoryModel, TagModel, article_tags


class SQLAlchemyArticleRepository(ArticleRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, m: ArticleModel) -> Article:
        return Article(
            id=m.id, slug=m.slug, title=m.title, excerpt=m.excerpt,
            content=m.content, cover_image_url=m.cover_image_url,
            author_id=m.author_id, category_id=m.category_id,
            status=ArticleStatus(m.status), is_featured=m.is_featured,
            reading_time_min=m.reading_time_min, views_count=m.views_count,
            meta_title=m.meta_title, meta_description=m.meta_description,
            published_at=m.published_at,
            tag_ids=[t.id for t in m.tags] if m.tags else [],
            created_at=m.created_at, updated_at=m.updated_at,
        )

    async def get_by_id(self, article_id: UUID) -> Article | None:
        r = await self._session.execute(
            select(ArticleModel).options(selectinload(ArticleModel.tags)).where(ArticleModel.id == article_id)
        )
        m = r.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def get_by_slug(self, slug: str) -> Article | None:
        r = await self._session.execute(
            select(ArticleModel).options(selectinload(ArticleModel.tags)).where(ArticleModel.slug == slug)
        )
        m = r.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def create(self, article: Article, tag_ids: list[UUID] | None = None) -> Article:
        now = datetime.now(timezone.utc).isoformat()
        m = ArticleModel(
            id=article.id, slug=article.slug, title=article.title,
            excerpt=article.excerpt, content=article.content,
            cover_image_url=article.cover_image_url,
            author_id=article.author_id, category_id=article.category_id,
            status=article.status.value, is_featured=article.is_featured,
            reading_time_min=article.reading_time_min, views_count=article.views_count,
            meta_title=article.meta_title, meta_description=article.meta_description,
            published_at=article.published_at, created_at=now, updated_at=now,
        )
        if tag_ids:
            r = await self._session.execute(select(TagModel).where(TagModel.id.in_(tag_ids)))
            m.tags = r.scalars().all()
        self._session.add(m)
        await self._session.flush()
        return self._to_entity(m)

    async def update(self, article: Article, tag_ids: list[UUID] | None = None) -> Article:
        r = await self._session.execute(
            select(ArticleModel).options(selectinload(ArticleModel.tags)).where(ArticleModel.id == article.id)
        )
        m = r.scalar_one_or_none()
        if not m:
            return article
        for f in ["slug", "title", "excerpt", "content", "cover_image_url",
                   "category_id", "status", "is_featured", "reading_time_min",
                   "views_count", "meta_title", "meta_description", "published_at"]:
            setattr(m, f, getattr(article, f))
        m.updated_at = datetime.now(timezone.utc).isoformat()
        if tag_ids is not None:
            tr = await self._session.execute(select(TagModel).where(TagModel.id.in_(tag_ids)))
            m.tags = tr.scalars().all()
        await self._session.flush()
        # Re-load with tags to get the updated relationship
        r = await self._session.execute(
            select(ArticleModel).options(selectinload(ArticleModel.tags)).where(ArticleModel.id == article.id)
        )
        m = r.scalar_one_or_none()
        return self._to_entity(m) if m else article

    async def delete(self, article_id: UUID) -> None:
        r = await self._session.execute(select(ArticleModel).where(ArticleModel.id == article_id))
        m = r.scalar_one_or_none()
        if m:
            await self._session.delete(m)
            await self._session.flush()

    async def list_articles(self, page: int = 1, limit: int = 6, category_slug: str | None = None,
                            tag_slug: str | None = None, search: str | None = None,
                            author_id: UUID | None = None, featured: bool | None = None,
                            status: str | None = None, sort: str = "published_at",
                            order: str = "desc") -> tuple[list[dict], int]:
        q = select(ArticleModel).options(
            selectinload(ArticleModel.author),
            selectinload(ArticleModel.category),
            selectinload(ArticleModel.tags),
        )
        cq = select(func.count()).select_from(ArticleModel)

        if category_slug:
            cat_sub = select(CategoryModel.id).where(CategoryModel.slug == category_slug).scalar_subquery()
            q = q.where(ArticleModel.category_id.in_(cat_sub))
            cq = cq.where(ArticleModel.category_id.in_(cat_sub))
        if tag_slug:
            tag_sub = select(TagModel.id).where(TagModel.slug == tag_slug).scalar_subquery()
            q = q.join(article_tags, ArticleModel.id == article_tags.c.article_id).where(article_tags.c.tag_id.in_(tag_sub))
            cq = cq.join(article_tags, ArticleModel.id == article_tags.c.article_id).where(article_tags.c.tag_id.in_(tag_sub))
        if search:
            f = or_(ArticleModel.title.ilike(f"%{search}%"), ArticleModel.excerpt.ilike(f"%{search}%"))
            q = q.where(f)
            cq = cq.where(f)
        if author_id:
            q = q.where(ArticleModel.author_id == author_id)
            cq = cq.where(ArticleModel.author_id == author_id)
        if featured is not None:
            q = q.where(ArticleModel.is_featured == featured)
            cq = cq.where(ArticleModel.is_featured == featured)
        if status:
            q = q.where(ArticleModel.status == status)
            cq = cq.where(ArticleModel.status == status)

        allowed_sorts = {"published_at", "created_at", "title", "views_count"}
        sc = getattr(ArticleModel, sort, ArticleModel.published_at) if sort in allowed_sorts else ArticleModel.published_at
        q = q.order_by(sc.desc() if order == "desc" else sc.asc())
        q = q.distinct()

        total = (await self._session.execute(cq.distinct())).scalar() or 0
        r = await self._session.execute(q.offset((page - 1) * limit).limit(limit))
        rows = r.scalars().all()

        items = []
        for m in rows:
            d = {
                "id": str(m.id), "slug": m.slug, "title": m.title,
                "excerpt": m.excerpt, "cover_image_url": m.cover_image_url,
                "author_id": str(m.author_id), "category_id": str(m.category_id),
                "status": m.status, "is_featured": m.is_featured,
                "reading_time_min": m.reading_time_min, "views_count": m.views_count,
                "meta_title": m.meta_title, "meta_description": m.meta_description,
                "published_at": m.published_at, "created_at": m.created_at,
                "updated_at": m.updated_at,
            }
            if m.author:
                d["author"] = {
                    "id": str(m.author.id), "first_name": m.author.first_name,
                    "last_name": m.author.last_name, "avatar_url": m.author.avatar_url,
                }
            if m.category:
                d["category"] = {
                    "id": str(m.category.id), "name": m.category.name,
                    "slug": m.category.slug, "color": m.category.color,
                }
            if m.tags:
                d["tags"] = [
                    {"id": str(t.id), "name": t.name, "slug": t.slug, "color": t.color}
                    for t in m.tags
                ]
            items.append(d)
        return items, total

    async def increment_views(self, article_id: UUID) -> int:
        r = await self._session.execute(select(ArticleModel).where(ArticleModel.id == article_id))
        m = r.scalar_one_or_none()
        if m:
            m.views_count = (m.views_count or 0) + 1
            await self._session.flush()
            return m.views_count
        return 0

    async def ensure_slug_unique(self, slug: str, exclude_id: UUID | None = None) -> str:
        base = slug
        counter = 1
        while True:
            q = select(ArticleModel).where(ArticleModel.slug == slug)
            if exclude_id:
                q = q.where(ArticleModel.id != exclude_id)
            r = await self._session.execute(q)
            if not r.scalar_one_or_none():
                return slug
            slug = f"{base}-{counter}"
            counter += 1


class SQLAlchemyCategoryRepository(CategoryRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, m: CategoryModel) -> Category:
        return Category(
            id=m.id, name=m.name, slug=m.slug, description=m.description or "",
            icon=m.icon or "", color=m.color or "#000000",
            sort_order=m.sort_order or 0,
            created_at=m.created_at, updated_at=m.updated_at,
        )

    async def get_by_id(self, category_id: UUID) -> Category | None:
        r = await self._session.execute(select(CategoryModel).where(CategoryModel.id == category_id))
        m = r.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def get_by_slug(self, slug: str) -> Category | None:
        r = await self._session.execute(select(CategoryModel).where(CategoryModel.slug == slug))
        m = r.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def create(self, category: Category) -> Category:
        now = datetime.now(timezone.utc).isoformat()
        m = CategoryModel(
            id=category.id, name=category.name, slug=category.slug,
            description=category.description, icon=category.icon,
            color=category.color, sort_order=category.sort_order,
            created_at=now, updated_at=now,
        )
        self._session.add(m)
        await self._session.flush()
        return self._to_entity(m)

    async def update(self, category: Category) -> Category:
        r = await self._session.execute(select(CategoryModel).where(CategoryModel.id == category.id))
        m = r.scalar_one_or_none()
        if not m:
            return category
        for f in ["name", "slug", "description", "icon", "color", "sort_order"]:
            setattr(m, f, getattr(category, f))
        m.updated_at = datetime.now(timezone.utc).isoformat()
        await self._session.flush()
        return self._to_entity(m)

    async def delete(self, category_id: UUID) -> None:
        r = await self._session.execute(select(CategoryModel).where(CategoryModel.id == category_id))
        m = r.scalar_one_or_none()
        if m:
            await self._session.delete(m)
            await self._session.flush()

    async def list_categories(self) -> list[Category]:
        r = await self._session.execute(
            select(CategoryModel).order_by(CategoryModel.sort_order.asc(), CategoryModel.name.asc())
        )
        return [self._to_entity(m) for m in r.scalars().all()]

    async def has_articles(self, category_id: UUID) -> bool:
        r = await self._session.execute(
            select(func.count()).select_from(ArticleModel).where(ArticleModel.category_id == category_id)
        )
        return (r.scalar() or 0) > 0


class SQLAlchemyTagRepository(TagRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, m: TagModel) -> Tag:
        return Tag(
            id=m.id, name=m.name, slug=m.slug,
            color=m.color or "#000000", created_at=m.created_at,
        )

    async def get_by_id(self, tag_id: UUID) -> Tag | None:
        r = await self._session.execute(select(TagModel).where(TagModel.id == tag_id))
        m = r.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def get_by_slug(self, slug: str) -> Tag | None:
        r = await self._session.execute(select(TagModel).where(TagModel.slug == slug))
        m = r.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def create(self, tag: Tag) -> Tag:
        now = datetime.now(timezone.utc).isoformat()
        m = TagModel(id=tag.id, name=tag.name, slug=tag.slug, color=tag.color, created_at=now)
        self._session.add(m)
        await self._session.flush()
        return self._to_entity(m)

    async def update(self, tag: Tag) -> Tag:
        r = await self._session.execute(select(TagModel).where(TagModel.id == tag.id))
        m = r.scalar_one_or_none()
        if not m:
            return tag
        for f in ["name", "slug", "color"]:
            setattr(m, f, getattr(tag, f))
        await self._session.flush()
        return self._to_entity(m)

    async def delete(self, tag_id: UUID) -> None:
        r = await self._session.execute(select(TagModel).where(TagModel.id == tag_id))
        m = r.scalar_one_or_none()
        if m:
            await self._session.delete(m)
            await self._session.flush()

    async def list_tags(self, search: str | None = None, limit: int = 50) -> list[Tag]:
        q = select(TagModel).order_by(TagModel.name.asc())
        if search:
            q = q.where(TagModel.name.ilike(f"%{search}%"))
        q = q.limit(limit)
        r = await self._session.execute(q)
        return [self._to_entity(m) for m in r.scalars().all()]
