from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.administration.infrastructure.models import SettingModel, ActivityLogModel


class SQLAlchemySettingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all(self) -> dict:
        r = await self._session.execute(select(SettingModel))
        models = r.scalars().all()
        return {m.key: {"id": str(m.id), "key": m.key, "value": m.value, "updated_by": str(m.updated_by) if m.updated_by else None, "updated_at": m.updated_at} for m in models}

    async def update_settings(self, settings: list[dict]) -> list[dict]:
        results = []
        for s in settings:
            key = s["key"]
            r = await self._session.execute(
                select(SettingModel).where(SettingModel.key == key)
            )
            m = r.scalar_one_or_none()
            if m:
                m.value = s["value"]
                m.updated_by = s.get("updated_by")
                m.updated_at = datetime.now(timezone.utc).isoformat()
            else:
                m = SettingModel(
                    key=key,
                    value=s["value"],
                    updated_by=s.get("updated_by"),
                    updated_at=datetime.now(timezone.utc).isoformat(),
                )
                self._session.add(m)
            results.append({"key": key, "value": s["value"]})
        await self._session.flush()
        return results


class SQLAlchemyActivityLogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_dict(self, m: ActivityLogModel) -> dict:
        return {
            "id": str(m.id),
            "user_id": str(m.user_id) if m.user_id else None,
            "action": m.action,
            "entity_type": m.entity_type,
            "entity_id": str(m.entity_id) if m.entity_id else None,
            "metadata": m.meta_data,
            "ip_address": m.ip_address,
            "created_at": m.created_at,
        }

    async def log(self, data: dict) -> dict:
        m = ActivityLogModel(
            user_id=data.get("user_id"),
            action=data["action"],
            entity_type=data.get("entity_type"),
            entity_id=data.get("entity_id"),
            meta_data=data.get("metadata", {}),
            ip_address=data.get("ip_address"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )
        self._session.add(m)
        await self._session.flush()
        return self._to_dict(m)

    async def list_entries(
        self,
        page: int = 1,
        limit: int = 20,
        user_id: UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
    ) -> tuple[list[dict], int]:
        q = select(ActivityLogModel)
        cq = select(func.count()).select_from(ActivityLogModel)

        if user_id:
            q = q.where(ActivityLogModel.user_id == user_id)
            cq = cq.where(ActivityLogModel.user_id == user_id)

        if action:
            q = q.where(ActivityLogModel.action == action)
            cq = cq.where(ActivityLogModel.action == action)

        if entity_type:
            q = q.where(ActivityLogModel.entity_type == entity_type)
            cq = cq.where(ActivityLogModel.entity_type == entity_type)

        q = q.order_by(ActivityLogModel.created_at.desc())

        total = (await self._session.execute(cq)).scalar() or 0
        r = await self._session.execute(q.offset((page - 1) * limit).limit(limit))
        items = [self._to_dict(m) for m in r.scalars().all()]
        return items, total
