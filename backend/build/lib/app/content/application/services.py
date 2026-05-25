from uuid import uuid4
from datetime import datetime, timezone
from math import ceil

from app.content.domain.entities import Article, Category, Tag, ArticleStatus
from app.content.domain.repositories import ArticleRepository, CategoryRepository, TagRepository
from app.content.domain import events as domain_events
from app.shared.events.event_bus import event_bus
from app.shared.exceptions import ConflictError, ForbiddenError, NotFoundError, BadRequestError
from app.shared.pagination import paginate


def _article_resp(a: Article) -> dict:
    return {
        "id": str(a.id), "slug": a.slug, "title": a.title,
        "excerpt": a.excerpt, "cover_image_url": a.cover_image_url,
        "author_id": str(a.author_id) if a.author_id else None,
        "category_id": str(a.category_id) if a.category_id else None,
        "status": a.status.value, "is_featured": a.is_featured,
        "reading_time_min": a.reading_time_min, "views_count": a.views_count,
        "meta_title": a.meta_title, "meta_description": a.meta_description,
        "published_at": a.published_at, "tag_ids": [str(t) for t in a.tag_ids],
        "created_at": a.created_at, "updated_at": a.updated_at,
    }


def _category_resp(c: Category) -> dict:
    return {
        "id": str(c.id), "name": c.name, "slug": c.slug,
        "description": c.description, "icon": c.icon,
        "color": c.color, "sort_order": c.sort_order,
        "article_count": c.article_count,
        "created_at": c.created_at, "updated_at": c.updated_at,
    }


def _tag_resp(t: Tag) -> dict:
    return {
        "id": str(t.id), "name": t.name, "slug": t.slug,
        "color": t.color, "article_count": t.article_count,
        "created_at": t.created_at,
    }


class ArticleService:
    def __init__(self, repo: ArticleRepository, category_repo: CategoryRepository, tag_repo: TagRepository):
        self._repo = repo
        self._category_repo = category_repo
        self._tag_repo = tag_repo

    async def create_article(self, author_id, title: str, excerpt: str, content: str,
                             cover_image_url: str | None = None, category_id=None,
                             tag_ids: list | None = None, status: str = "draft",
                             is_featured: bool = False, meta_title: str | None = None,
                             meta_description: str | None = None) -> dict:
        if category_id:
            cat = await self._category_repo.get_by_id(category_id)
            if not cat:
                raise NotFoundError("Category not found")
        if tag_ids:
            for tid in tag_ids:
                t = await self._tag_repo.get_by_id(tid)
                if not t:
                    raise NotFoundError(f"Tag {tid} not found")

        slug = Article.generate_slug(title)
        slug = await self._repo.ensure_slug_unique(slug)
        reading_time = Article.calculate_reading_time(content)

        try:
            article_status = ArticleStatus(status)
        except ValueError:
            raise BadRequestError(f"Invalid status: {status}")

        published_at = None
        if article_status == ArticleStatus.PUBLISHED:
            published_at = datetime.now(timezone.utc).isoformat()

        article = Article(
            id=uuid4(), slug=slug, title=title, excerpt=excerpt,
            content=content, cover_image_url=cover_image_url,
            author_id=author_id, category_id=category_id,
            status=article_status, is_featured=is_featured,
            reading_time_min=reading_time,
            meta_title=meta_title, meta_description=meta_description,
            published_at=published_at,
            tag_ids=tag_ids or [],
        )
        article = await self._repo.create(article, tag_ids=tag_ids)
        await event_bus.publish(domain_events.article_created(
            str(article.id), str(author_id), title, article_status.value
        ))
        return _article_resp(article)

    async def update_article(self, article_id, author_id, **kwargs) -> dict:
        article = await self._repo.get_by_id(article_id)
        if not article:
            raise NotFoundError("Article not found")

        changed_fields = []
        for k, v in kwargs.items():
            if v is not None and hasattr(article, k):
                if k == "status":
                    try:
                        v = ArticleStatus(v)
                    except ValueError:
                        raise BadRequestError(f"Invalid status: {v}")
                if k == "category_id" and v:
                    cat = await self._category_repo.get_by_id(v)
                    if not cat:
                        raise NotFoundError("Category not found")
                if k == "tag_ids":
                    continue  # handled separately
                old_val = getattr(article, k)
                setattr(article, k, v)
                if old_val != v:
                    changed_fields.append(k)

        tag_ids = kwargs.get("tag_ids")
        if tag_ids is not None:
            for tid in tag_ids:
                t = await self._tag_repo.get_by_id(tid)
                if not t:
                    raise NotFoundError(f"Tag {tid} not found")
            article.tag_ids = tag_ids
            if "tag_ids" not in changed_fields:
                changed_fields.append("tag_ids")

        if "title" in kwargs and kwargs["title"] is not None:
            slug = Article.generate_slug(kwargs["title"])
            slug = await self._repo.ensure_slug_unique(slug, exclude_id=article.id)
            article.slug = slug

        if "content" in kwargs and kwargs["content"] is not None:
            article.reading_time_min = Article.calculate_reading_time(kwargs["content"])

        article = await self._repo.update(article, tag_ids=tag_ids)
        if changed_fields:
            await event_bus.publish(domain_events.article_updated(
                str(article.id), str(author_id), changed_fields
            ))
        return _article_resp(article)

    async def publish_article(self, article_id, current_user) -> dict:
        article = await self._repo.get_by_id(article_id)
        if not article:
            raise NotFoundError("Article not found")

        if current_user.role not in ("super_admin", "admin", "editor"):
            if str(article.author_id) != str(current_user.id):
                raise ForbiddenError("You can only publish your own articles")

        if article.is_published:
            raise BadRequestError("Article is already published")

        article.status = ArticleStatus.PUBLISHED
        article.published_at = datetime.now(timezone.utc).isoformat()
        article = await self._repo.update(article)
        await event_bus.publish(domain_events.article_published(
            str(article.id), str(article.author_id), article.title, article.published_at
        ))
        return _article_resp(article)

    async def unpublish_article(self, article_id, current_user) -> dict:
        article = await self._repo.get_by_id(article_id)
        if not article:
            raise NotFoundError("Article not found")

        if current_user.role not in ("super_admin", "admin", "editor"):
            raise ForbiddenError("Only editors and admins can unpublish articles")

        article.status = ArticleStatus.DRAFT
        article.published_at = None
        article = await self._repo.update(article)
        return _article_resp(article)

    async def delete_article(self, article_id, current_user) -> None:
        article = await self._repo.get_by_id(article_id)
        if not article:
            raise NotFoundError("Article not found")

        if current_user.role not in ("super_admin", "admin"):
            if str(article.author_id) != str(current_user.id):
                raise ForbiddenError("You can only delete your own articles")

        await self._repo.delete(article_id)
        await event_bus.publish(domain_events.article_deleted(
            str(article_id), str(current_user.id)
        ))

    async def get_article(self, article_id) -> dict:
        article = await self._repo.get_by_id(article_id)
        if not article:
            raise NotFoundError("Article not found")
        return _article_resp(article)

    async def get_article_by_slug(self, slug: str) -> dict:
        article = await self._repo.get_by_slug(slug)
        if not article:
            raise NotFoundError("Article not found")
        return _article_resp(article)

    async def list_articles(self, page: int = 1, limit: int = 6, **filters) -> dict:
        items, total = await self._repo.list_articles(page=page, limit=limit, **filters)
        return paginate(items, total, page, limit)

    async def record_view(self, article_id: str, fingerprint: str, referrer: str = "") -> dict:
        article = await self._repo.get_by_id(article_id)
        if not article:
            raise NotFoundError("Article not found")
        views = await self._repo.increment_views(article.id)
        await event_bus.publish(domain_events.article_viewed(article_id, fingerprint, referrer))
        return {"views_count": views}

    async def get_featured(self, limit: int = 5) -> dict:
        items, total = await self._repo.list_articles(
            page=1, limit=limit, featured=True, status="published", sort="published_at", order="desc"
        )
        return paginate(items, total, 1, limit)


class CategoryService:
    def __init__(self, repo: CategoryRepository, article_repo: ArticleRepository):
        self._repo = repo
        self._article_repo = article_repo

    async def create_category(self, name: str, description: str = "", icon: str = "",
                              color: str = "#000000", sort_order: int = 0) -> dict:
        existing = await self._repo.get_by_slug(Category.generate_slug(name))
        if existing:
            raise ConflictError("Category with this name already exists")

        slug = Category.generate_slug(name)
        category = Category(
            id=uuid4(), name=name, slug=slug, description=description,
            icon=icon, color=color, sort_order=sort_order,
        )
        category = await self._repo.create(category)
        await event_bus.publish(domain_events.category_created(str(category.id), name))
        return _category_resp(category)

    async def update_category(self, category_id, **kwargs) -> dict:
        category = await self._repo.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found")

        changed_fields = []
        for k, v in kwargs.items():
            if v is not None and hasattr(category, k):
                old_val = getattr(category, k)
                setattr(category, k, v)
                if old_val != v:
                    changed_fields.append(k)

        if "name" in kwargs and kwargs["name"] is not None:
            category.slug = Category.generate_slug(kwargs["name"])

        category = await self._repo.update(category)
        if changed_fields:
            await event_bus.publish(domain_events.category_updated(str(category.id), changed_fields))
        return _category_resp(category)

    async def delete_category(self, category_id) -> None:
        category = await self._repo.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found")

        if await self._repo.has_articles(category_id):
            raise ConflictError("Cannot delete category with existing articles")

        await self._repo.delete(category_id)
        await event_bus.publish(domain_events.category_deleted(str(category_id)))

    async def get_category(self, category_id) -> dict:
        category = await self._repo.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found")
        return _category_resp(category)

    async def get_category_by_slug(self, slug: str) -> dict:
        category = await self._repo.get_by_slug(slug)
        if not category:
            raise NotFoundError("Category not found")
        return _category_resp(category)

    async def list_categories(self) -> dict:
        categories = await self._repo.list_categories()
        return {"data": [_category_resp(c) for c in categories]}


class TagService:
    def __init__(self, repo: TagRepository):
        self._repo = repo

    async def create_tag(self, name: str, color: str = "#000000") -> dict:
        existing = await self._repo.get_by_slug(Tag.generate_slug(name))
        if existing:
            raise ConflictError("Tag with this name already exists")

        slug = Tag.generate_slug(name)
        tag = Tag(id=uuid4(), name=name, slug=slug, color=color)
        tag = await self._repo.create(tag)
        await event_bus.publish(domain_events.tag_created(str(tag.id), name))
        return _tag_resp(tag)

    async def update_tag(self, tag_id, **kwargs) -> dict:
        tag = await self._repo.get_by_id(tag_id)
        if not tag:
            raise NotFoundError("Tag not found")

        for k, v in kwargs.items():
            if v is not None and hasattr(tag, k):
                setattr(tag, k, v)

        if "name" in kwargs and kwargs["name"] is not None:
            tag.slug = Tag.generate_slug(kwargs["name"])

        tag = await self._repo.update(tag)
        return _tag_resp(tag)

    async def delete_tag(self, tag_id) -> None:
        tag = await self._repo.get_by_id(tag_id)
        if not tag:
            raise NotFoundError("Tag not found")

        await self._repo.delete(tag_id)
        await event_bus.publish(domain_events.tag_deleted(str(tag_id)))

    async def get_tag(self, tag_id) -> dict:
        tag = await self._repo.get_by_id(tag_id)
        if not tag:
            raise NotFoundError("Tag not found")
        return _tag_resp(tag)

    async def list_tags(self, search: str | None = None, limit: int = 50) -> dict:
        tags = await self._repo.list_tags(search=search, limit=limit)
        return {"data": [_tag_resp(t) for t in tags]}
