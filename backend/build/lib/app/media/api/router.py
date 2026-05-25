from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import get_session
from app.shared.auth.dependencies import require_roles
from app.identity.infrastructure.models import UserModel
from app.media.infrastructure.repositories import SQLAlchemyMediaRepository
from app.media.application.services import MediaService

router = APIRouter(prefix="/media", tags=["Media"])


def _svc(db) -> MediaService:
    return MediaService(SQLAlchemyMediaRepository(db))


@router.get("")
async def list_media(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    mime_type: str | None = None,
    uploaded_by: UUID | None = None,
    db: AsyncSession = Depends(get_session),
):
    return await _svc(db).list_media(
        page=page, limit=limit, search=search, mime_type=mime_type, uploaded_by=uploaded_by
    )


@router.post("/upload", status_code=201)
async def upload_media(
    file: UploadFile = File(...),
    alt_text: str = Form(""),
    u: UserModel = Depends(require_roles("super_admin", "admin", "author")),
    db: AsyncSession = Depends(get_session),
):
    file_data = await file.read()
    return await _svc(db).upload(
        file_data=file_data,
        filename=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by=u.id,
        alt_text=alt_text,
    )


@router.patch("/{media_id}")
async def update_media(
    media_id: UUID,
    alt_text: str | None = None,
    u: UserModel = Depends(require_roles("super_admin", "admin", "author")),
    db: AsyncSession = Depends(get_session),
):
    return await _svc(db).update_media(
        media_id=media_id,
        alt_text=alt_text,
        current_user_id=u.id,
        current_user_role=u.role,
    )


@router.delete("/{media_id}")
async def delete_media(
    media_id: UUID,
    u: UserModel = Depends(require_roles("super_admin", "admin", "author")),
    db: AsyncSession = Depends(get_session),
):
    await _svc(db).delete_media(
        media_id=media_id,
        current_user_id=u.id,
        current_user_role=u.role,
    )
    return {"message": "Media deleted successfully"}
