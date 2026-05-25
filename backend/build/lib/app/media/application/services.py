from uuid import UUID
from datetime import datetime, timezone
from io import BytesIO

from app.media.infrastructure.repositories import SQLAlchemyMediaRepository
from app.media.domain import events as domain_events
from app.shared.events.event_bus import event_bus
from app.shared.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.shared.storage.factory import get_storage_provider
from app.shared.pagination import paginate
from app.config import get_settings


class MediaService:
    def __init__(self, repo: SQLAlchemyMediaRepository):
        self._repo = repo
        self._settings = get_settings()

    async def upload(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        uploaded_by: UUID,
        alt_text: str = "",
    ) -> dict:
        if mime_type not in self._settings.allowed_mime_types_list:
            raise BadRequestError(f"MIME type {mime_type} is not allowed")

        if len(file_data) > self._settings.MAX_FILE_SIZE:
            raise BadRequestError(
                f"File size exceeds maximum of {self._settings.MAX_FILE_SIZE} bytes"
            )

        width = None
        height = None
        if mime_type.startswith("image/") and mime_type != "image/svg+xml":
            try:
                from PIL import Image

                img = Image.open(BytesIO(file_data))
                width, height = img.size
            except Exception:
                pass

        storage = get_storage_provider()
        import os
        from uuid import uuid4

        ext = os.path.splitext(filename)[1]
        stored_name = f"{uuid4()}{ext}"
        path = f"media/{stored_name}"
        url = await storage.save(file_data, path)

        now = datetime.now(timezone.utc).isoformat()
        data = {
            "filename": stored_name,
            "original_name": filename,
            "mime_type": mime_type,
            "file_size": len(file_data),
            "width": width,
            "height": height,
            "url": url,
            "alt_text": alt_text,
            "uploaded_by": uploaded_by,
            "created_at": now,
        }
        result = await self._repo.create(data)

        await event_bus.publish(
            domain_events.media_uploaded(
                str(result["id"]),
                str(uploaded_by),
                filename,
                len(file_data),
            )
        )
        return result

    async def list_media(
        self,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        mime_type: str | None = None,
        uploaded_by: UUID | None = None,
    ) -> dict:
        items, total = await self._repo.list_media(
            page=page,
            limit=min(limit, 100),
            search=search,
            mime_type=mime_type,
            uploaded_by=uploaded_by,
        )
        return paginate(items, total, page, min(limit, 100))

    async def update_media(
        self,
        media_id: UUID,
        alt_text: str | None,
        current_user_id: UUID,
        current_user_role: str,
    ) -> dict:
        media = await self._repo.get_by_id(media_id)
        if not media:
            raise NotFoundError("Media not found")

        if media["uploaded_by"] != str(current_user_id) and current_user_role not in (
            "admin",
            "super_admin",
        ):
            raise ForbiddenError("You can only update your own media")

        update_data = {}
        if alt_text is not None:
            update_data["alt_text"] = alt_text

        result = await self._repo.update(media_id, update_data)
        return result

    async def delete_media(
        self,
        media_id: UUID,
        current_user_id: UUID,
        current_user_role: str,
    ) -> None:
        media = await self._repo.get_by_id(media_id)
        if not media:
            raise NotFoundError("Media not found")

        if media["uploaded_by"] != str(current_user_id) and current_user_role not in (
            "admin",
            "super_admin",
        ):
            raise ForbiddenError("You can only delete your own media")

        storage = get_storage_provider()
        filename = media.get("filename", "")
        if filename:
            await storage.delete(f"media/{filename}")

        await self._repo.delete(media_id)

        await event_bus.publish(
            domain_events.media_deleted(str(media_id), str(current_user_id))
        )
