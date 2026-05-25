from uuid import uuid4
from datetime import datetime, timezone, timedelta
import hashlib
from math import ceil

from app.identity.domain.entities import User, Role
from app.identity.domain.repositories import UserRepository
from app.identity.domain import events as domain_events
from app.shared.auth.jwt_handler import encode_access_token, encode_refresh_token, decode_refresh_token
from app.shared.auth.password_hasher import hash_password, verify_password
from app.shared.events.event_bus import event_bus
from app.shared.exceptions import ConflictError, AuthenticationError, ForbiddenError, BadRequestError, NotFoundError
from app.config import get_settings


def _user_resp(u: User) -> dict:
    return {"id": str(u.id), "email": u.email, "first_name": u.first_name, "last_name": u.last_name, "role": u.role.value, "avatar_url": u.avatar_url, "created_at": u.created_at}

def _user_detail(u: User) -> dict:
    return {"id": str(u.id), "email": u.email, "first_name": u.first_name, "last_name": u.last_name, "role": u.role.value, "avatar_url": u.avatar_url, "bio": u.bio, "github_handle": u.github_handle, "twitter_handle": u.twitter_handle, "is_active": u.is_active, "email_verified": u.email_verified, "last_login_at": u.last_login_at, "created_at": u.created_at}


async def _store_refresh_token(user_id, refresh_token: str):
    from app.identity.infrastructure.models import RefreshTokenModel
    from app.shared.database import async_session
    settings = get_settings()
    h = hashlib.sha256(refresh_token.encode()).hexdigest()
    exp = (datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRY_DAYS)).isoformat()
    async with async_session() as s:
        s.add(RefreshTokenModel(user_id=user_id, token_hash=h, expires_at=exp))
        await s.commit()


class AuthApplicationService:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    async def register(self, email: str, password: str, first_name: str, last_name: str) -> dict:
        if await self._repo.get_by_email(email):
            raise ConflictError("Email already registered")
        user = User(id=uuid4(), email=email, password_hash=hash_password(password), first_name=first_name, last_name=last_name, role=Role.AUTHOR)
        user = await self._repo.create(user)
        at, rt = encode_access_token(str(user.id), user.role.value), encode_refresh_token(str(user.id))
        await _store_refresh_token(user.id, rt)
        await event_bus.publish(domain_events.user_registered(str(user.id), email, user.role.value))
        return {"user": _user_resp(user), "access_token": at, "refresh_token": rt}

    async def login(self, email: str, password: str, ip: str = "") -> dict:
        user = await self._repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise ForbiddenError("Account deactivated")
        await self._repo.update_last_login(user.id)
        at, rt = encode_access_token(str(user.id), user.role.value), encode_refresh_token(str(user.id))
        await _store_refresh_token(user.id, rt)
        user = await self._repo.get_by_id(user.id)
        await event_bus.publish(domain_events.user_logged_in(str(user.id), ip))
        return {"user": _user_resp(user), "access_token": at, "refresh_token": rt}

    async def refresh(self, refresh_token: str) -> dict:
        payload = decode_refresh_token(refresh_token)
        uid = payload.get("sub")
        h = hashlib.sha256(refresh_token.encode()).hexdigest()
        from app.identity.infrastructure.models import RefreshTokenModel
        from app.shared.database import async_session
        from sqlalchemy import select
        async with async_session() as s:
            r = await s.execute(select(RefreshTokenModel).where(RefreshTokenModel.token_hash == h, RefreshTokenModel.is_revoked == False))
            rt = r.scalar_one_or_none()
            if not rt: raise AuthenticationError("Invalid or revoked refresh token")
            rt.is_revoked = True; await s.commit()
        user = await self._repo.get_by_id(uid)
        if not user or not user.is_active: raise AuthenticationError("User not found or deactivated")
        at, nrt = encode_access_token(str(user.id), user.role.value), encode_refresh_token(str(user.id))
        await _store_refresh_token(user.id, nrt)
        return {"access_token": at, "refresh_token": nrt}

    async def logout(self, refresh_token: str) -> None:
        h = hashlib.sha256(refresh_token.encode()).hexdigest()
        from app.identity.infrastructure.models import RefreshTokenModel
        from app.shared.database import async_session
        from sqlalchemy import select
        async with async_session() as s:
            r = await s.execute(select(RefreshTokenModel).where(RefreshTokenModel.token_hash == h))
            rt = r.scalar_one_or_none()
            if rt: rt.is_revoked = True; await s.commit()

    async def forgot_password(self, email: str) -> None:
        pass  # Email sending would be implemented here

    async def reset_password(self, token: str, password: str) -> None:
        pass  # Token verification would be implemented here

    async def change_password(self, user_id, current_password: str, new_password: str) -> None:
        user = await self._repo.get_by_id(user_id)
        if not user: raise NotFoundError("User not found")
        if not verify_password(current_password, user.password_hash): raise BadRequestError("Current password is incorrect")
        user.password_hash = hash_password(new_password)
        await self._repo.update(user)
        await event_bus.publish(domain_events.user_password_reset(str(user.id)))


class UserApplicationService:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    async def get_me(self, user_id) -> dict:
        u = await self._repo.get_by_id(user_id)
        if not u: raise NotFoundError("User not found")
        return _user_detail(u)

    async def update_me(self, user_id, **kw) -> dict:
        u = await self._repo.get_by_id(user_id)
        if not u: raise NotFoundError("User not found")
        for k, v in kw.items():
            if v is not None and hasattr(u, k): setattr(u, k, v)
        u = await self._repo.update(u)
        return _user_detail(u)

    async def list_users(self, current_user: User, **f) -> dict:
        users, total = await self._repo.list_users(**f)
        p, l = f.get("page", 1), f.get("limit", 20)
        return {"data": [_user_resp(u) for u in users], "meta": {"total": total, "page": p, "limit": l, "total_pages": ceil(total/l) if l else 0}}

    async def get_user(self, user_id) -> dict:
        u = await self._repo.get_by_id(user_id)
        if not u: raise NotFoundError("User not found")
        return _user_detail(u)

    async def create_user(self, cur: User, email: str, password: str, first_name: str, last_name: str, role: str = "author", is_active: bool = True) -> dict:
        if await self._repo.get_by_email(email): raise ConflictError("Email already registered")
        try: re = Role(role)
        except ValueError: raise BadRequestError(f"Invalid role: {role}")
        if cur.role == Role.ADMIN and re == Role.SUPER_ADMIN: raise ForbiddenError("Cannot assign super_admin role")
        u = User(id=uuid4(), email=email, password_hash=hash_password(password), first_name=first_name, last_name=last_name, role=re, is_active=is_active)
        u = await self._repo.create(u)
        await event_bus.publish(domain_events.user_registered(str(u.id), email, role))
        return _user_detail(u)

    async def update_user(self, cur: User, user_id, **kw) -> dict:
        u = await self._repo.get_by_id(user_id)
        if not u: raise NotFoundError("User not found")
        if not cur.can_manage_user(u): raise ForbiddenError("Cannot modify this user")
        old_role = u.role.value
        for k, v in kw.items():
            if v is not None and hasattr(u, k):
                if k == "role":
                    try: v = Role(v)
                    except ValueError: raise BadRequestError(f"Invalid role: {v}")
                    if cur.role == Role.ADMIN and v == Role.SUPER_ADMIN: raise ForbiddenError("Cannot assign super_admin role")
                setattr(u, k, v)
        u = await self._repo.update(u)
        if "role" in kw and kw["role"] != old_role:
            await event_bus.publish(domain_events.user_role_changed(str(u.id), old_role, u.role.value, str(cur.id)))
        return _user_detail(u)

    async def delete_user(self, cur: User, user_id) -> None:
        u = await self._repo.get_by_id(user_id)
        if not u: raise NotFoundError("User not found")
        if not cur.can_manage_user(u): raise ForbiddenError("Cannot deactivate this user")
        u.is_active = False
        await self._repo.update(u)
