from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.media.infrastructure.models import MediaModel


class SQLAlchemyMediaRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_dict(self, m: MediaModel) -> dict:
        d = {
            "id": str(m.id),
            "filename": m.filename,
            "original_name": m.original_name,
            "mime_type": m.mime_type,
            "file_size": m.file_size,
            "width": m.width,
            "height": m.height,
            "url": m.url,
            "alt_text": m.alt_text,
            "uploaded_by": str(m.uploaded_by),
            "created_at": m.created_at,
        }
        if m.uploader:
            d["uploader"] = {
                "id": str(m.uploader.id),
                "first_name": m.uploader.first_name,
                "last_name": m.uploader.last_name,
                "email": m.uploader.email,
            }
        return d

    async def get_by_id(self, media_id: UUID) -> dict | None:
        r = await self._session.execute(
            select(MediaModel).where(MediaModel.id == media_id)
        )
        m = r.scalar_one_or_none()
        return self._to_dict(m) if m else None

    async def create(self, data: dict) -> dict:
        m = MediaModel(
            filename=data["filename"],
            original_name=data["original_name"],
            mime_type=data["mime_type"],
            file_size=data["file_size"],
            width=data.get("width"),
            height=data.get("height"),
            url=data["url"],
            alt_text=data.get("alt_text", ""),
            uploaded_by=data["uploaded_by"],
            created_at=data.get("created_at"),
        )
        self._session.add(m)
        await self._session.flush()
        return self._to_dict(m)

    async def update(self, media_id: UUID, data: dict) -> dict | None:
        r = await self._session.execute(
            select(MediaModel).where(MediaModel.id == media_id)
        )
        m = r.scalar_one_or_none()
        if not m:
            return None
        for key, value in data.items():
            if hasattr(m, key):
                setattr(m, key, value)
        await self._session.flush()
        return self._to_dict(m)

    async def delete(self, media_id: UUID) -> bool:
        r = await self._session.execute(
            select(MediaModel).where(MediaModel.id == media_id)
        )
        m = r.scalar_one_or_none()
        if not m:
            return False
        await self._session.delete(m)
        await self._session.flush()
        return True

    async def list_media(
        self,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        mime_type: str | None = None,
        uploaded_by: UUID | None = None,
    ) -> tuple[list[dict], int]:
        q = select(MediaModel)
        cq = select(func.count()).select_from(MediaModel)

        if search:
            filter_expr = or_(
                MediaModel.original_name.ilike(f"%{search}%"),
                MediaModel.alt_text.ilike(f"%{search}%"),
            )
            q = q.where(filter_expr)
            cq = cq.where(filter_expr)

        if mime_type:
            q = q.where(MediaModel.mime_type == mime_type)
            cq = cq.where(MediaModel.mime_type == mime_type)

        if uploaded_by:
            q = q.where(MediaModel.uploaded_by == uploaded_by)
            cq = cq.where(MediaModel.uploaded_by == uploaded_by)

        q = q.order_by(MediaModel.created_at.desc())

        total = (await self._session.execute(cq)).scalar() or 0
        r = await self._session.execute(q.offset((page - 1) * limit).limit(limit))
        items = [self._to_dict(m) for m in r.scalars().all()]
        return items, total
