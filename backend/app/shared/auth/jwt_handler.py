from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.shared.exceptions import AuthenticationError
from app.config import get_settings

_settings = get_settings()


def encode_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=_settings.JWT_ACCESS_EXPIRY_MINUTES)
    payload = {"sub": user_id, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, _settings.JWT_ACCESS_SECRET, algorithm="HS256")


def encode_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=_settings.JWT_REFRESH_EXPIRY_DAYS)
    payload = {"sub": user_id, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, _settings.JWT_REFRESH_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, _settings.JWT_ACCESS_SECRET, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        return payload
    except JWTError as e:
        raise AuthenticationError("Invalid or expired token") from e


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, _settings.JWT_REFRESH_SECRET, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        return payload
    except JWTError as e:
        raise AuthenticationError("Invalid or expired refresh token") from e
