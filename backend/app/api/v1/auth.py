from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import random
import time
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, decode_access_token
from app.models.user import User
from app.models.field import Field
from app.models.carbon_report import CarbonReport
from app.models.soil_record import SoilRecord
from app.services.auth import AuthService
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["认证"])

# 两步验证码内存存储: {user_id: {"code": str, "expires": float}}
_2fa_codes: dict[str, dict] = {}
_2fa_CODE_TTL = 300  # 5 分钟有效


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    phone: str | None = None
    area: str | None = None


@router.get("/me", response_model=UserOut)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


@router.put("/me")
async def update_me(
    data: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if data.phone is not None:
        user.phone = data.phone
    if data.area is not None:
        user.area = data.area
    await db.flush()
    return {"ok": True}


@router.get("/stats")
async def my_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """当前用户的统计数据"""
    user_id = current_user["sub"]

    # 服务天数
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    service_days = 0
    if user and user.created_at:
        delta = datetime.now(timezone.utc) - user.created_at.replace(tzinfo=timezone.utc)
        service_days = max(1, delta.days)

    # 田块数
    field_count = (await db.execute(
        select(func.count()).select_from(Field).where(Field.user_id == user_id)
    )).scalar() or 0

    # 碳汇总计
    carbon_result = await db.execute(
        select(func.coalesce(func.sum(CarbonReport.carbon_amount), 0))
        .select_from(CarbonReport).where(CarbonReport.user_id == user_id)
    )
    total_carbon = round(float(carbon_result.scalar() or 0), 1)

    # 最新数据更新时间（取田块/土壤记录/碳汇报告中最近的 created_at）
    timestamps = []
    for model in (Field, SoilRecord, CarbonReport):
        q = select(model.created_at).where(model.user_id == user_id).order_by(model.created_at.desc()).limit(1)
        row = (await db.execute(q)).scalar()
        if row:
            timestamps.append(row)
    last_sync = max(timestamps).isoformat() if timestamps else None

    return {
        "service_days": int(service_days),
        "field_count": int(field_count),
        "total_carbon_tco2e": total_carbon,
        "last_sync": last_sync,
        "role": current_user.get("role", "farmer"),
    }


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        result = await svc.register(data.username, data.password, data.phone, data.area)
        return TokenResponse(access_token=result["access_token"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login")
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        user = await svc.authenticate(data.username, data.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    # 检查两步验证
    if user.two_factor_enabled:
        code = f"{random.randint(0, 999999):06d}"
        _2fa_codes[str(user.id)] = {"code": code, "expires": time.time() + _2fa_CODE_TTL}
        temp_token = create_access_token(
            {"sub": str(user.id), "purpose": "2fa"},
            expires_delta=timedelta(minutes=5),
        )
        # TODO: 生产环境替换为真实短信服务
        phone_hint = user.phone[:3] + "****" + user.phone[-4:] if user.phone and len(user.phone) >= 11 else "未绑定手机"
        print(f"[开发模式] 两步验证码已发送至 {phone_hint}: {code}")
        return {"need_2fa": True, "temp_token": temp_token, "phone_hint": phone_hint}
    # 未开启两步验证，直接返回 token
    from app.api.v1.settings import record_login_device
    await record_login_device(str(user.id), request.headers.get("user-agent", ""), request.client.host if request.client else "", db)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)


class Verify2FARequest(BaseModel):
    temp_token: str
    code: str


@router.post("/verify-2fa", response_model=TokenResponse)
async def verify_2fa(data: Verify2FARequest, request: Request, db: AsyncSession = Depends(get_db)):
    payload = decode_access_token(data.temp_token)
    if not payload or payload.get("purpose") != "2fa":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="临时令牌无效或已过期")
    user_id = payload["sub"]
    record = _2fa_codes.get(user_id)
    if not record or record["code"] != data.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")
    if time.time() > record["expires"]:
        _2fa_codes.pop(user_id, None)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码已过期，请重新获取")
    _2fa_codes.pop(user_id, None)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    from app.api.v1.settings import record_login_device
    await record_login_device(str(user.id), request.headers.get("user-agent", ""), request.client.host if request.client else "", db)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    svc = AuthService(db)
    try:
        await svc.change_password(current_user["sub"], data.old_password, data.new_password)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ───────── 忘记密码 ─────────

# 重置密码验证码: {phone: {"code": str, "expires": float}}
_reset_codes: dict[str, dict] = {}
_reset_CODE_TTL = 300


class ForgotPasswordRequest(BaseModel):
    phone: str


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == data.phone))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该手机号未注册")
    code = f"{random.randint(0, 999999):06d}"
    _reset_codes[data.phone] = {"code": code, "expires": time.time() + _reset_CODE_TTL}
    # TODO: 生产环境替换为真实短信服务
    print(f"[开发模式] 密码重置验证码已发送至 {data.phone}: {code}")
    return {"ok": True, "message": "验证码已发送"}


class ResetPasswordRequest(BaseModel):
    phone: str
    code: str
    new_password: str


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    record = _reset_codes.get(data.phone)
    if not record or record["code"] != data.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")
    if time.time() > record["expires"]:
        _reset_codes.pop(data.phone, None)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码已过期")
    _reset_codes.pop(data.phone, None)
    if len(data.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码至少6位")
    result = await db.execute(select(User).where(User.phone == data.phone))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    from app.core.security import hash_password
    user.hashed_password = hash_password(data.new_password)
    await db.flush()
    return {"ok": True, "message": "密码重置成功"}
