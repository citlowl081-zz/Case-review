"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, chat, knowledge, session, user
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.logging import LoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown events."""
    # Startup: create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize default admin user
    from app.core.database import async_session_factory
    from app.services.auth_service import init_admin_user
    async with async_session_factory() as db:
        await init_admin_user(db)
        await db.commit()

    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="临床试验文档智能审核与知识库问答 RAG Agent 系统",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Custom Middleware ---
app.add_middleware(LoggingMiddleware)
# RateLimitMiddleware is added but can be conditionally bypassed in dev
# app.add_middleware(RateLimitMiddleware)


# --- Routers ---
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(user.router, prefix="/api/users", tags=["用户"])
app.include_router(session.router, prefix="/api/sessions", tags=["会话"])
app.include_router(chat.router, prefix="/api/chat", tags=["问答"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])


@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查接口."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# ── Static files (production mode: serve built frontend) ──
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
FRONTEND_DIST = os.path.abspath(FRONTEND_DIST)

if os.path.isdir(FRONTEND_DIST):
    # Mount static assets (JS, CSS, images) at /assets/
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend SPA — return index.html for all non-API routes."""
        # Skip API routes
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")

        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)

        return {"message": "Frontend not built. Run: cd frontend && npm run build"}
