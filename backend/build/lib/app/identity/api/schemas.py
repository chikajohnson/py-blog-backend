from pydantic import BaseModel, EmailStr
from uuid import UUID


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    avatar_url: str | None = None
    created_at: str | None = None

class UserDetailResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    avatar_url: str | None = None
    bio: str = ""
    github_handle: str | None = None
    twitter_handle: str | None = None
    is_active: bool = True
    email_verified: bool = False
    last_login_at: str | None = None
    created_at: str | None = None

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str

class MessageResponse(BaseModel):
    message: str

class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    github_handle: str | None = None
    twitter_handle: str | None = None

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str = "author"
    is_active: bool = True

class UpdateUserRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    bio: str | None = None
    github_handle: str | None = None
    twitter_handle: str | None = None
