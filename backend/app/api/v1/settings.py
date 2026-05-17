from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import random
import time
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.notification_setting import NotificationSetting
from app.models.team_member import TeamMember
from app.models.device import Device
from app.models.login_device import LoginDevice
from app.models.notification import Notification
from app.models.field import Field
from app.models.carbon_report import CarbonReport
from app.models.remote_sensing_ts import RemoteSensingTimeseries

router = APIRouter(prefix="/settings", tags=["设置"])

# 验证码内存存储: {phone: {"code": str, "expires": float}}
_sms_codes: dict[str, dict] = {}
_CODE_TTL = 300  # 验证码 5 分钟有效


# ───────── 实名认证 ─────────

class VerifyIdentityRequest(BaseModel):
    real_name: str
    id_card: str


@router.post("/verify-identity")
async def verify_identity(
    data: VerifyIdentityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if user.verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已实名认证")
    # 验证身份证号格式（18位）
    import re
    if not re.match(r'^\d{17}[\dXx]$', data.id_card):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="身份证号格式不正确")
    user.real_name = data.real_name
    user.id_card = data.id_card
    user.verified = True
    await db.flush()
    return {"ok": True, "message": "实名认证成功"}


@router.get("/verify-status")
async def get_verify_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return {
        "verified": user.verified,
        "real_name": user.real_name[:2] + "****" if user.real_name else None,
        "id_card": user.id_card[:4] + "**********" + user.id_card[-4:] if user.id_card else None,
    }


# ───────── 手机号变更 ─────────

class ChangePhoneRequest(BaseModel):
    new_phone: str
    code: str


@router.put("/phone")
async def change_phone(
    data: ChangePhoneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # 验证码校验
    record = _sms_codes.get(data.new_phone)
    if not record or record["code"] != data.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")
    if time.time() > record["expires"]:
        _sms_codes.pop(data.new_phone, None)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码已过期，请重新获取")
    _sms_codes.pop(data.new_phone, None)  # 验证通过后立即失效
    if len(data.new_phone) < 11:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="手机号格式不正确")
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    # 检查手机号是否已注册
    existing = await db.execute(select(User).where(User.phone == data.new_phone, User.id != user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该手机号已被其他账号绑定")
    user.phone = data.new_phone
    await db.flush()
    return {"ok": True, "message": "手机号修改成功"}


class SendCodeRequest(BaseModel):
    phone: str


@router.post("/send-code")
async def send_code(
    data: SendCodeRequest,
    current_user: dict = Depends(get_current_user),
):
    if len(data.phone) < 11:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="手机号格式不正确")
    code = f"{random.randint(0, 999999):06d}"
    _sms_codes[data.phone] = {"code": code, "expires": time.time() + _CODE_TTL}
    # TODO: 生产环境替换为真实短信服务（阿里云/腾讯云短信）
    print(f"[开发模式] 验证码已发送至 {data.phone}: {code}")
    return {"ok": True, "message": "验证码已发送，请查收短信"}


# ───────── 通知设置 ─────────

NOTIFY_TYPES = ["system", "weather", "field", "carbon", "alarm"]


class NotificationUpdate(BaseModel):
    enabled: bool | None = None
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    push_enabled: bool | None = None


@router.get("/notifications")
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["sub"]
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.user_id == user_id)
    )
    settings = {s.notify_type: s for s in result.scalars().all()}

    items = []
    labels = {
        "system": "系统通知",
        "weather": "气象预警",
        "field": "田块动态",
        "carbon": "碳汇报告",
        "alarm": "设备告警",
    }
    for t in NOTIFY_TYPES:
        s = settings.get(t)
        items.append({
            "type": t,
            "label": labels.get(t, t),
            "enabled": s.enabled if s else True,
            "email_enabled": s.email_enabled if s else False,
            "sms_enabled": s.sms_enabled if s else False,
            "push_enabled": s.push_enabled if s else True,
        })
    return items


@router.put("/notifications/{notify_type}")
async def update_notification(
    notify_type: str,
    data: NotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if notify_type not in NOTIFY_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未知通知类型")
    user_id = current_user["sub"]
    result = await db.execute(
        select(NotificationSetting).where(
            NotificationSetting.user_id == user_id,
            NotificationSetting.notify_type == notify_type,
        )
    )
    setting = result.scalar_one_or_none()
    if not setting:
        setting = NotificationSetting(user_id=user_id, notify_type=notify_type)
        db.add(setting)
    if data.enabled is not None:
        setting.enabled = data.enabled
    if data.email_enabled is not None:
        setting.email_enabled = data.email_enabled
    if data.sms_enabled is not None:
        setting.sms_enabled = data.sms_enabled
    if data.push_enabled is not None:
        setting.push_enabled = data.push_enabled
    await db.flush()
    return {"ok": True}


# ───────── 团队成员 ─────────

class AddTeamMemberRequest(BaseModel):
    username: str
    display_name: str | None = None
    role: str = "viewer"


@router.get("/team")
async def get_team(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(TeamMember).where(TeamMember.owner_id == current_user["sub"])
    )
    return [
        {
            "id": m.id,
            "username": m.username,
            "display_name": m.display_name,
            "role": m.role,
            "status": m.status,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in result.scalars().all()
    ]


@router.post("/team")
async def add_team_member(
    data: AddTeamMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if data.role not in ("admin", "editor", "viewer"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色无效")
    # 验证用户名是否存在
    target = await db.execute(select(User).where(User.username == data.username))
    if not target.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    member = TeamMember(
        owner_id=current_user["sub"],
        username=data.username,
        display_name=data.display_name or data.username,
        role=data.role,
    )
    db.add(member)
    await db.flush()
    return {"ok": True, "id": member.id}


@router.delete("/team/{member_id}")
async def remove_team_member(
    member_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.id == member_id,
            TeamMember.owner_id == current_user["sub"],
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")
    await db.delete(member)
    await db.flush()
    return {"ok": True}


# ───────── 设备管理 ─────────

class AddDeviceRequest(BaseModel):
    name: str
    device_type: str
    model: str | None = None
    serial_number: str | None = None


@router.get("/devices")
async def get_devices(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Device).where(Device.user_id == current_user["sub"])
    )
    return [
        {
            "id": d.id,
            "name": d.name,
            "device_type": d.device_type,
            "model": d.model,
            "serial_number": d.serial_number,
            "status": d.status,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in result.scalars().all()
    ]


@router.post("/devices")
async def add_device(
    data: AddDeviceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    device = Device(
        user_id=current_user["sub"],
        name=data.name,
        device_type=data.device_type,
        model=data.model,
        serial_number=data.serial_number,
        status="online",
        last_seen=datetime.now(timezone.utc),
    )
    db.add(device)
    await db.flush()
    return {"ok": True, "id": device.id}


@router.delete("/devices/{device_id}")
async def remove_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.user_id == current_user["sub"],
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    await db.delete(device)
    await db.flush()
    return {"ok": True}


# ───────── 两步验证 ─────────

class Toggle2FARequest(BaseModel):
    enabled: bool


@router.put("/2fa")
async def toggle_2fa(
    data: Toggle2FARequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.two_factor_enabled = data.enabled
    await db.flush()
    return {"ok": True, "enabled": user.two_factor_enabled}


@router.get("/2fa")
async def get_2fa_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return {"enabled": user.two_factor_enabled}


# ───────── 注销账号 ─────────

class DeleteAccountRequest(BaseModel):
    password: str
    confirm: str  # 必须输入 "确认删除"


@router.post("/delete-account")
async def delete_account(
    data: DeleteAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if data.confirm != "确认删除":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请输入「确认删除」以确认")
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    # 验证密码
    from app.core.security import verify_password
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="密码错误")
    # 软删除
    user.is_active = False
    user.username = f"deleted_{user.id[:8]}"
    await db.flush()
    return {"ok": True, "message": "账号已注销"}


# ───────── 登录设备管理 ─────────

def _parse_user_agent(ua: str) -> str:
    """从 User-Agent 字符串解析出浏览器/系统描述"""
    if not ua:
        return "未知设备"
    browser = "Unknown"
    os_name = "Unknown"
    if "Edg/" in ua:
        browser = "Edge"
    elif "Chrome/" in ua:
        browser = "Chrome"
    elif "Firefox/" in ua:
        browser = "Firefox"
    elif "Safari/" in ua and "Chrome/" not in ua:
        browser = "Safari"
    if "Windows NT 10" in ua:
        os_name = "Windows 11"
    elif "Windows NT 6.3" in ua:
        os_name = "Windows 8.1"
    elif "Windows" in ua:
        os_name = "Windows"
    elif "Mac OS X" in ua:
        os_name = "macOS"
    elif "Android" in ua:
        os_name = "Android"
    elif "iPhone" in ua or "iPad" in ua:
        os_name = "iOS"
    elif "Linux" in ua:
        os_name = "Linux"
    return f"{browser} / {os_name}"


async def record_login_device(user_id: str, user_agent: str, ip_address: str, db: AsyncSession):
    """登录成功后记录设备信息"""
    device_name = _parse_user_agent(user_agent)
    # 将同用户的其他设备标记为非当前
    await db.execute(
        update(LoginDevice).where(LoginDevice.user_id == user_id).values(is_current=False)
    )
    device = LoginDevice(
        user_id=user_id,
        device_name=device_name,
        ip_address=ip_address,
        is_current=True,
    )
    db.add(device)
    await db.flush()
    return device


@router.get("/login-devices")
async def get_login_devices(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(LoginDevice)
        .where(LoginDevice.user_id == current_user["sub"])
        .order_by(LoginDevice.last_seen.desc())
    )
    return [
        {
            "id": d.id,
            "device_name": d.device_name,
            "ip_address": d.ip_address,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "is_current": d.is_current,
        }
        for d in result.scalars().all()
    ]


@router.delete("/login-devices/{device_id}")
async def revoke_login_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(LoginDevice).where(
            LoginDevice.id == device_id,
            LoginDevice.user_id == current_user["sub"],
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    await db.delete(device)
    await db.flush()
    return {"ok": True}


# ───────── 通知消息 ─────────

async def create_notification(user_id: str, text: str, notify_type: str = "info", db: AsyncSession = None):
    """创建通知消息（供其他模块调用）"""
    if db is None:
        return
    notif = Notification(user_id=user_id, text=text, notify_type=notify_type)
    db.add(notif)
    await db.flush()
    return notif


@router.get("/messages")
async def get_messages(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["sub"]
    # 管理员同时看到自己的通知和用户反馈
    if current_user.get("role") == "admin":
        stmt = select(Notification).where(
            (Notification.user_id == user_id) | (Notification.user_id == "admin")
        ).order_by(Notification.created_at.desc()).limit(30)
    else:
        stmt = select(Notification).where(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    now = datetime.now(timezone.utc)
    items = []
    for n in result.scalars().all():
        delta = now - n.created_at.replace(tzinfo=timezone.utc)
        if delta.days > 0:
            time_str = f"{delta.days} 天前"
        elif delta.seconds >= 3600:
            time_str = f"{delta.seconds // 3600} 小时前"
        elif delta.seconds >= 60:
            time_str = f"{delta.seconds // 60} 分钟前"
        else:
            time_str = "刚刚"
        items.append({
            "id": n.id,
            "text": n.text,
            "type": n.notify_type,
            "time": time_str,
            "read": n.read,
            "created_at": n.created_at.isoformat(),
        })
    return items


@router.put("/messages/{message_id}/read")
async def mark_message_read(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == message_id,
            Notification.user_id == current_user["sub"],
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    notif.read = True
    await db.flush()
    return {"ok": True}


# ───────── 数据导出 ─────────

@router.get("/export/fields")
async def export_fields(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    import json, io
    result = await db.execute(
        select(Field).where(Field.user_id == current_user["sub"])
    )
    fields = []
    for f in result.scalars().all():
        fields.append({
            "id": f.id,
            "name": f.name,
            "area_ha": f.area_ha,
            "crop_type": f.crop_type,
            "geometry": f.geometry,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        })
    buf = io.BytesIO()
    buf.write(json.dumps(fields, ensure_ascii=False, indent=2).encode("utf-8"))
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=fields.json"},
    )


@router.get("/export/carbon")
async def export_carbon(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    import csv, io
    result = await db.execute(
        select(CarbonReport).where(CarbonReport.user_id == current_user["sub"]).order_by(CarbonReport.created_at.desc())
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["报告ID", "田块", "秸秆量(kg)", "碳汇量(tCO2e)", "生成时间"])
    for r in result.scalars().all():
        writer.writerow([
            r.id, r.field_name or "", r.straw_amount, r.carbon_amount,
            r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
        ])
    output = io.BytesIO()
    output.write(buf.getvalue().encode("utf-8-sig"))
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=carbon_reports.csv"},
    )


@router.get("/export/ndvi")
async def export_ndvi(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    import csv, io
    result = await db.execute(
        select(RemoteSensingTimeseries).where(RemoteSensingTimeseries.user_id == current_user["sub"])
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["田块ID", "日期", "NDVI", "EVI", "NDWI", "地表温度", "云覆盖率"])
    for r in result.scalars().all():
        writer.writerow([
            r.field_id, r.date, r.ndvi, r.evi, r.ndwi, r.surface_temp, r.cloud_cover,
        ])
    output = io.BytesIO()
    output.write(buf.getvalue().encode("utf-8-sig"))
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ndvi_timeseries.csv"},
    )
