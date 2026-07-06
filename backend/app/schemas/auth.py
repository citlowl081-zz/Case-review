"""Auth-related request/response schemas."""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    confirm_password: str = Field(..., description="确认密码")


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfoResponse"


class UserInfoResponse(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool
    created_at: str
