"""User routes — get current user info."""
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserInfoResponse

router = APIRouter()


@router.get("/me", response_model=UserInfoResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息."""
    return UserInfoResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
    )
