from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.identity.domain.entities import User, Role
from app.identity.domain.repositories import UserRepository
from app.identity.infrastructure.models import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, m: UserModel) -> User:
        return User(id=m.id, email=m.email, password_hash=m.password_hash, first_name=m.first_name, last_name=m.last_name, avatar_url=m.avatar_url, bio=m.bio or "", github_handle=m.github_handle, twitter_handle=m.twitter_handle, role=Role(m.role), is_active=m.is_active, email_verified=m.email_verified, last_login_at=m.last_login_at, created_at=m.created_at, updated_at=m.updated_at)

    async def get_by_id(self, user_id: UUID) -> User | None:
        r = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        m = r.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def get_by_email(self, email: str) -> User | None:
        r = await self._session.execute(select(UserModel).where(UserModel.email == email))
        m = r.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def create(self, user: User) -> User:
        now = datetime.now(timezone.utc).isoformat()
        m = UserModel(id=user.id, email=user.email, password_hash=user.password_hash, first_name=user.first_name, last_name=user.last_name, avatar_url=user.avatar_url, bio=user.bio, github_handle=user.github_handle, twitter_handle=user.twitter_handle, role=user.role.value, is_active=user.is_active, email_verified=user.email_verified, created_at=now, updated_at=now)
        self._session.add(m)
        await self._session.flush()
        return self._to_entity(m)

    async def update(self, user: User) -> User:
        r = await self._session.execute(select(UserModel).where(UserModel.id == user.id))
        m = r.scalar_one_or_none()
        if not m: return user
        for f in ["first_name", "last_name", "avatar_url", "bio", "github_handle", "twitter_handle", "is_active", "email_verified", "password_hash"]:
            setattr(m, f, getattr(user, f))
        m.role = user.role.value
        m.updated_at = datetime.now(timezone.utc).isoformat()
        await self._session.flush()
        return self._to_entity(m)

    async def list_users(self, page=1, limit=20, role=None, search=None, is_active=None, sort="created_at", order="desc") -> tuple[list[User], int]:
        q = select(UserModel); cq = select(func.count()).select_from(UserModel)
        if role: q = q.where(UserModel.role == role); cq = cq.where(UserModel.role == role)
        if search: f = or_(UserModel.first_name.ilike(f"%{search}%"), UserModel.last_name.ilike(f"%{search}%"), UserModel.email.ilike(f"%{search}%")); q = q.where(f); cq = cq.where(f)
        if is_active is not None: q = q.where(UserModel.is_active == is_active); cq = cq.where(UserModel.is_active == is_active)
        sc = getattr(UserModel, sort, UserModel.created_at) if sort in {"created_at", "email", "first_name", "role"} else UserModel.created_at
        q = q.order_by(sc.desc() if order == "desc" else sc.asc())
        total = (await self._session.execute(cq)).scalar() or 0
        r = await self._session.execute(q.offset((page-1)*limit).limit(limit))
        return [self._to_entity(m) for m in r.scalars().all()], total

    async def update_last_login(self, user_id: UUID) -> None:
        r = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        m = r.scalar_one_or_none()
        if m: m.last_login_at = datetime.now(timezone.utc).isoformat(); await self._session.flush()
