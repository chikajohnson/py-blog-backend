from pydantic import BaseModel
from uuid import UUID


class CreateArticleRequest(BaseModel):
    title: str
    excerpt: str
    content: str
    cover_image_url: str | None = None
    category_id: UUID | None = None
    tag_ids: list[UUID] | None = None
    status: str = "draft"
    is_featured: bool = False
    meta_title: str | None = None
    meta_description: str | None = None


class UpdateArticleRequest(BaseModel):
    title: str | None = None
    excerpt: str | None = None
    content: str | None = None
    cover_image_url: str | None = None
    category_id: UUID | None = None
    tag_ids: list[UUID] | None = None
    status: str | None = None
    is_featured: bool | None = None
    meta_title: str | None = None
    meta_description: str | None = None


class RecordViewRequest(BaseModel):
    fingerprint: str
    referrer: str = ""


class CreateCategoryRequest(BaseModel):
    name: str
    description: str = ""
    icon: str = ""
    color: str = "#000000"
    sort_order: int = 0


class UpdateCategoryRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    sort_order: int | None = None


class CreateTagRequest(BaseModel):
    name: str
    color: str = "#000000"


class UpdateTagRequest(BaseModel):
    name: str | None = None
    color: str | None = None
