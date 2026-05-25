from uuid import UUID
from datetime import datetime, timezone

from app.administration.infrastructure.repositories import (
    SQLAlchemySettingRepository,
    SQLAlchemyActivityLogRepository,
)
from app.administration.domain import events as domain_events
from app.shared.events.event_bus import event_bus
from app.shared.pagination import paginate


class SettingsService:
    def __init__(self, repo: SQLAlchemySettingRepository):
        self._repo = repo

    async def get_settings(self) -> dict:
        return await self._repo.get_all()

    async def update_settings(
        self,
        settings: list[dict],
        updated_by: UUID,
    ) -> dict:
        for s in settings:
            s["updated_by"] = updated_by
        results = await self._repo.update_settings(settings)

        keys_changed = [r["key"] for r in results]
        await event_bus.publish(
            domain_events.settings_updated(str(updated_by), keys_changed)
        )

        return {"updated": results}


class ActivityLogService:
    def __init__(self, repo: SQLAlchemyActivityLogRepository):
        self._repo = repo

    async def log(self, data: dict) -> dict:
        return await self._repo.log(data)

    async def list_entries(
        self,
        page: int = 1,
        limit: int = 20,
        user_id: UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
    ) -> dict:
        items, total = await self._repo.list_entries(
            page=page,
            limit=min(limit, 100),
            user_id=user_id,
            action=action,
            entity_type=entity_type,
        )
        return paginate(items, total, page, min(limit, 100))
