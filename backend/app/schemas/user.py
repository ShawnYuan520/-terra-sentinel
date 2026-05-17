from pydantic import BaseModel
from datetime import datetime


class UserOut(BaseModel):
    id: str
    username: str
    role: str
    phone: str | None
    area: str | None
    real_name: str | None = None
    id_card: str | None = None
    verified: bool = False
    two_factor_enabled: bool = False
    avatar_url: str | None = None
    bio: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListOut(BaseModel):
    total: int
    items: list[UserOut]