from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import hashlib

from app.shared.database import get_session
from app.shared.auth.dependencies import get_current_user, require_roles
from app.identity.infrastructure.models import UserModel
from app.identity.domain.entities import Role
from app.content.infrastructure.repositories import SQLAlchemyArticleRepository, SQLAlchemyCategoryRepository, SQLAlchemyTagRepository
from app.content.application.services import ArticleService, CategoryService, TagService
from app.content.api.schemas import *

router = APIRouter(tags=["Articles"])
categories_router = APIRouter(tags=["Categories"])
tags_router = APIRouter(tags=["Tags"])
search_router = APIRouter(tags=["Search"])


def _article_svc(db): return ArticleService(SQLAlchemyArticleRepository(db), SQLAlchemyCategoryRepository(db), SQLAlchemyTagRepository(db))
def _category_svc(db): return CategoryService(SQLAlchemyCategoryRepository(db), SQLAlchemyArticleRepository(db))
def _tag_svc(db): return TagService(SQLAlchemyTagRepository(db))


# --- Articles ---

@router.get("/articles")
async def list_articles(
    page: int = Query(1, ge=1), limit: int = Query(6, ge=1, le=50),
    category: str | None = None, tag: str | None = None,
    search: str | None = None, author: str | None = None,
    featured: bool | None = None, sort: str = "published_at", order: str = "desc",
    db: AsyncSession = Depends(get_session),
):
    filters = {"category_slug": category, "tag_slug": tag, "search": search,
               "author_id": UUID(author) if author else None,
               "featured": featured, "sort": sort, "order": order}
    filters = {k: v for k, v in filters.items() if v is not None}
    return await _article_svc(db).list_articles(page=page, limit=limit, **filters)


@router.get("/articles/{slug}")
async def get_article(slug: str, db: AsyncSession = Depends(get_session)):
    return await _article_svc(db).get_article_by_slug(slug)


@router.post("/articles", status_code=201)
async def create_article(
    b: CreateArticleRequest,
    u: UserModel = Depends(require_roles("super_admin", "admin", "editor", "author")),
    db: AsyncSession = Depends(get_session),
):
    return await _article_svc(db).create_article(
        author_id=u.id, author_role=u.role, title=b.title, excerpt=b.excerpt,
        content=b.content, cover_image_url=b.cover_image_url, category_id=b.category_id,
        tag_ids=b.tag_ids, status=b.status, is_featured=b.is_featured,
        meta_title=b.meta_title, meta_description=b.meta_description,
    )


@router.patch("/articles/{article_id}")
async def update_article(
    article_id: str, b: UpdateArticleRequest,
    u: UserModel = Depends(require_roles("super_admin", "admin", "editor", "author")),
    db: AsyncSession = Depends(get_session),
):
    return await _article_svc(db).update_article(article_id, u.id, u.role, **b.model_dump(exclude_none=True))


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: str,
    u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    await _article_svc(db).delete_article(article_id, u.id)
    return {"message": "Article deleted successfully"}


@router.post("/articles/{article_id}/view")
async def record_article_view(
    article_id: str, b: RecordViewRequest, request: Request,
    db: AsyncSession = Depends(get_session),
):
    fp = hashlib.sha256((request.client.host if request.client else "unknown").encode()).hexdigest()
    return await _article_svc(db).record_view(article_id, fp, b.referrer)


# --- Categories ---

@categories_router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_session)):
    return await _category_svc(db).list_categories()


@categories_router.get("/categories/{slug}")
async def get_category(slug: str, page: int = 1, limit: int = 6, db: AsyncSession = Depends(get_session)):
    return await _category_svc(db).get_category_by_slug(slug, page=page, limit=limit)


@categories_router.post("/categories", status_code=201)
async def create_category(
    b: CreateCategoryRequest,
    u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    return await _category_svc(db).create_category(name=b.name, description=b.description, icon=b.icon, color=b.color, sort_order=b.sort_order)


@categories_router.patch("/categories/{category_id}")
async def update_category(
    category_id: str, b: UpdateCategoryRequest,
    u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    return await _category_svc(db).update_category(category_id, **b.model_dump(exclude_none=True))


@categories_router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    await _category_svc(db).delete_category(category_id)
    return {"message": "Category deleted successfully"}


# --- Tags ---

@tags_router.get("/tags")
async def list_tags(search: str | None = None, limit: int = Query(50, ge=1, le=100), db: AsyncSession = Depends(get_session)):
    return await _tag_svc(db).list_tags(search=search, limit=limit)


@tags_router.get("/tags/{slug}")
async def get_tag(slug: str, page: int = 1, limit: int = 6, db: AsyncSession = Depends(get_session)):
    return await _tag_svc(db).get_tag_by_slug(slug, page=page, limit=limit)


@tags_router.post("/tags", status_code=201)
async def create_tag(
    b: CreateTagRequest,
    u: UserModel = Depends(require_roles("super_admin", "admin", "editor")),
    db: AsyncSession = Depends(get_session),
):
    return await _tag_svc(db).create_tag(name=b.name, color=b.color)


@tags_router.patch("/tags/{tag_id}")
async def update_tag(
    tag_id: str, b: UpdateTagRequest,
    u: UserModel = Depends(require_roles("super_admin", "admin", "editor")),
    db: AsyncSession = Depends(get_session),
):
    return await _tag_svc(db).update_tag(tag_id, **b.model_dump(exclude_none=True))


@tags_router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: str,
    u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    await _tag_svc(db).delete_tag(tag_id)
    return {"message": "Tag deleted successfully"}


# --- Search ---

@search_router.get("/search")
async def search_articles(
    q: str = Query(..., min_length=2), page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50), category: str | None = None,
    tag: str | None = None, sort: str = "relevance",
    db: AsyncSession = Depends(get_session),
):
    from math import ceil
    repo = SQLAlchemyArticleRepository(db)
    items, total = await repo.list_articles(page=page, limit=limit, search=q, category_slug=category, tag_slug=tag)
    return {"data": items, "meta": {"total": total, "page": page, "limit": limit, "total_pages": ceil(total / limit) if limit > 0 else 0, "query": q}}
