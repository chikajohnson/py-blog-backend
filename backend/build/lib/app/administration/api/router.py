from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.shared.database import get_session
from app.shared.auth.dependencies import require_roles
from app.identity.infrastructure.models import UserModel
from app.administration.infrastructure.repositories import (
    SQLAlchemySettingRepository,
    SQLAlchemyActivityLogRepository,
)
from app.administration.application.services import SettingsService, ActivityLogService

# ── Settings router ───────────────────────────────────────────────────

settings_router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingItem(BaseModel):
    key: str
    value: dict


class UpdateSettingsRequest(BaseModel):
    settings: list[SettingItem]


@settings_router.get("")
async def get_settings(
    _u: UserModel = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_session),
):
    svc = SettingsService(SQLAlchemySettingRepository(db))
    return await svc.get_settings()


@settings_router.patch("")
async def update_settings(
    b: UpdateSettingsRequest,
    u: UserModel = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_session),
):
    svc = SettingsService(SQLAlchemySettingRepository(db))
    settings_data = [s.model_dump() for s in b.settings]
    return await svc.update_settings(settings_data, updated_by=u.id)


# ── Activity log router ───────────────────────────────────────────────

activity_log_router = APIRouter(prefix="/activity-log", tags=["Activity Log"])


@activity_log_router.get("")
async def list_activity_entries(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    _u: UserModel = Depends(require_roles("super_admin", "admin")),
    db: AsyncSession = Depends(get_session),
):
    svc = ActivityLogService(SQLAlchemyActivityLogRepository(db))
    return await svc.list_entries(
        page=page, limit=limit, user_id=user_id, action=action, entity_type=entity_type
    )


# ── Health router ─────────────────────────────────────────────────────

health_router = APIRouter(tags=["Health"])


@health_router.get("/health")
async def health_check(db: AsyncSession = Depends(get_session)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        return {"status": "unhealthy", "database": "disconnected", "error": str(exc)}
