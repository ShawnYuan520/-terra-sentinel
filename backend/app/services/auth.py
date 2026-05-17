"""认证服务"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, username: str, password: str, phone: str = None, area: str = None) -> dict:
        result = await self.db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise ValueError("用户名已存在")
        user = User(username=username, hashed_password=hash_password(password),
                    phone=phone, area=area)
        self.db.add(user)
        await self.db.flush()
        token = create_access_token({"sub": user.id, "role": user.role})
        return {"access_token": token, "token_type": "bearer"}

    async def authenticate(self, username: str, password: str) -> User:
        """验证用户名密码，返回 User 对象（供 2FA 流程使用）"""
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("用户名或密码错误")
        return user

    async def login(self, username: str, password: str) -> str:
        user = await self.authenticate(username, password)
        return create_access_token(data={"sub": str(user.id), "role": user.role})

    async def change_password(self, user_id: str, old_pw: str, new_pw: str) -> None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("用户不存在")
        if not verify_password(old_pw, user.hashed_password):
            raise ValueError("当前密码错误")
        user.hashed_password = hash_password(new_pw)
        await self.db.flush()
