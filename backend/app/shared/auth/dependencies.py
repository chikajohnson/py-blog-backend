from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.shared.database import get_session
from app.shared.auth.jwt_handler import decode_access_token
from app.shared.exceptions import AuthenticationError, ForbiddenError
from app.identity.infrastructure.models import UserModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
) -> UserModel:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise ForbiddenError("Account deactivated")
    return user


def require_roles(*roles: str):
    async def _check(user: UserModel = Depends(get_current_user)) -> UserModel:
        if user.role not in roles:
            raise ForbiddenError("Insufficient permissions")
        return user
    return _check
