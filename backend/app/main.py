from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import asyncio

from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.v1 import api_router
import app.models  # noqa: F401 确保 Base.metadata 发现所有表

settings = get_settings()


def _migrate_users_columns(conn):
    """给 users 表补上新增字段（SQLite 不支持 IF NOT EXISTS ADD COLUMN）。"""
    from sqlalchemy import text
    # 获取已有列名
    result = conn.execute(text("PRAGMA table_info(users)"))
    existing = {row[1] for row in result.fetchall()}
    new_cols = {
        "real_name": "TEXT",
        "id_card": "TEXT",
        "verified": "BOOLEAN DEFAULT 0",
        "two_factor_enabled": "BOOLEAN DEFAULT 0",
        "avatar_url": "TEXT",
        "bio": "TEXT",
    }
    for col, typedef in new_cols.items():
        if col not in existing:
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {typedef}"))
    conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # SQLite: 给 users 表补新增字段（create_all 不会 ALTER 已有表）
        if settings.DATABASE_URL.startswith("sqlite"):
            await conn.run_sync(_migrate_users_columns)
    # 预初始化 GEE（避免首次请求等待）
    try:
        from app.services.gee.gee_service import _init_gee
        import threading
        t = threading.Thread(target=_init_gee, daemon=True)
        t.start()
    except Exception:
        pass
    yield
    from app.services.raster import close_all_rasters
    close_all_rasters()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# GZip 压缩 — 减少响应体积 60-80%
app.add_middleware(GZipMiddleware, minimum_size=500)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求超时中间件 — 防止慢请求拖垮整个服务
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    timeout = 30.0  # 30 秒超时
    try:
        start = time.time()
        response = await asyncio.wait_for(call_next(request), timeout=timeout)
        elapsed = time.time() - start
        if elapsed > 3.0:
            pass  # 慢请求仅在日志中标记
        return response
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={"detail": "请求超时，请重试", "timeout_s": timeout},
        )


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "error": str(exc)[:200]},
    )


app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
