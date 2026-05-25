from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_session
from app.shared.auth.dependencies import get_current_user, require_roles
from app.identity.infrastructure.models import UserModel
from app.identity.infrastructure.repositories import SQLAlchemyUserRepository
from app.identity.application.services import AuthApplicationService, UserApplicationService
from app.identity.api.schemas import *

router = APIRouter(prefix="/auth", tags=["Auth"])

def _auth(db): return AuthApplicationService(SQLAlchemyUserRepository(db))
def _user(db): return UserApplicationService(SQLAlchemyUserRepository(db))

@router.post("/register", status_code=201)
async def register(b: RegisterRequest, db: AsyncSession = Depends(get_session)):
    return await _auth(db).register(b.email, b.password, b.first_name, b.last_name)

@router.post("/login")
async def login(b: LoginRequest, req: Request, db: AsyncSession = Depends(get_session)):
    return await _auth(db).login(b.email, b.password, req.client.host if req.client else "")

@router.post("/refresh")
async def refresh(b: RefreshRequest, db: AsyncSession = Depends(get_session)):
    return await _auth(db).refresh(b.refresh_token)

@router.post("/logout")
async def logout(b: LogoutRequest, db: AsyncSession = Depends(get_session)):
    await _auth(db).logout(b.refresh_token)
    return {"message": "Logged out successfully"}

@router.post("/forgot-password")
async def forgot_password(b: ForgotPasswordRequest, db: AsyncSession = Depends(get_session)):
    await _auth(db).forgot_password(b.email)
    return {"message": "If an account with that email exists, a reset link has been sent."}

@router.post("/reset-password")
async def reset_password(b: ResetPasswordRequest, db: AsyncSession = Depends(get_session)):
    await _auth(db).reset_password(b.token, b.password)
    return {"message": "Password reset successfully"}

@router.post("/verify-email")
async def verify_email():
    return {"message": "Email verified successfully"}

@router.get("/me")
async def get_me(u: UserModel = Depends(get_current_user)):
    return {"id": str(u.id), "email": u.email, "first_name": u.first_name, "last_name": u.last_name, "role": u.role, "avatar_url": u.avatar_url, "bio": u.bio or "", "github_handle": u.github_handle, "twitter_handle": u.twitter_handle, "is_active": u.is_active, "email_verified": u.email_verified, "last_login_at": u.last_login_at, "created_at": u.created_at}

@router.patch("/me")
async def update_me(b: UpdateProfileRequest, u: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return await _user(db).update_me(u.id, **b.model_dump(exclude_none=True))

@router.patch("/me/password")
async def change_password(b: ChangePasswordRequest, u: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    await _auth(db).change_password(u.id, b.current_password, b.new_password)
    return {"message": "Password changed successfully"}

users_router = APIRouter(prefix="/users", tags=["Users"])

@users_router.get("")
async def list_users(page: int = 1, limit: int = 20, role: str | None = None, search: str | None = None, is_active: bool | None = None, sort: str = "created_at", order: str = "desc", cur: UserModel = Depends(require_roles("super_admin", "admin")), db: AsyncSession = Depends(get_session)):
    ue = await SQLAlchemyUserRepository(db).get_by_id(cur.id)
    return await _user(db).list_users(ue, page=page, limit=min(limit,100), role=role, search=search, is_active=is_active, sort=sort, order=order)

@users_router.get("/{user_id}")
async def get_user(user_id: str, cur: UserModel = Depends(require_roles("super_admin", "admin")), db: AsyncSession = Depends(get_session)):
    return await _user(db).get_user(user_id)

@users_router.post("", status_code=201)
async def create_user(b: CreateUserRequest, cur: UserModel = Depends(require_roles("super_admin", "admin")), db: AsyncSession = Depends(get_session)):
    ue = await SQLAlchemyUserRepository(db).get_by_id(cur.id)
    return await _user(db).create_user(ue, b.email, b.password, b.first_name, b.last_name, b.role, b.is_active)

@users_router.patch("/{user_id}")
async def update_user(user_id: str, b: UpdateUserRequest, cur: UserModel = Depends(require_roles("super_admin", "admin")), db: AsyncSession = Depends(get_session)):
    ue = await SQLAlchemyUserRepository(db).get_by_id(cur.id)
    return await _user(db).update_user(ue, user_id, **b.model_dump(exclude_none=True))

@users_router.delete("/{user_id}")
async def delete_user(user_id: str, cur: UserModel = Depends(require_roles("super_admin")), db: AsyncSession = Depends(get_session)):
    ue = await SQLAlchemyUserRepository(db).get_by_id(cur.id)
    await _user(db).delete_user(ue, user_id)
    return {"message": "User deactivated successfully"}
