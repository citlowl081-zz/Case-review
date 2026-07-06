"""Authentication service — admin initialization and user management."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from app.models.user import User
from app.core.security import hash_password
from app.core.config import settings


async def init_admin_user(db: AsyncSession) -> None:
    """Ensure the default admin account exists on startup.

    Raises ValueError if ADMIN_PASSWORD is not configured.
    """
    if not settings.ADMIN_PASSWORD:
        raise ValueError(
            "ADMIN_PASSWORD 未配置！请在 .env 文件中设置 ADMIN_PASSWORD。\n"
            "示例: ADMIN_PASSWORD=your-strong-password-here"
        )

    result = await db.execute(
        select(User).where(User.username == settings.ADMIN_USERNAME)
    )
    admin = result.scalar_one_or_none()

    if admin is None:
        admin = User(
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
        )
        db.add(admin)
        await db.flush()
        logger.warning(
            f"Admin user '{settings.ADMIN_USERNAME}' created. "
            f"请立即登录并修改默认密码！"
        )
    else:
        logger.info(f"Admin user '{settings.ADMIN_USERNAME}' already exists.")
