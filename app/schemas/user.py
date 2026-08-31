"""用户相关 Pydantic 模型：注册、登录、用户信息返回。"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional

from app.schemas.common import Role


# 注册请求体
class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=80)  # 【问题19】与数据库 VARCHAR(80) 对齐
    password: str
    role: Role = Role.student
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)   # 姓名（可选）
    email: Optional[str] = Field(default=None, min_length=1, max_length=120)  # 邮箱（可选）

    # 【新增】密码强度校验：至少 8 位，且同时包含字母和数字
    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少为 8 位")
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        # 【问题20】bcrypt 5.0 对超 72 字节的输入会抛 ValueError，按字节校验（兼顾中文等多字节字符）
        if len(v.encode("utf-8")) > 72:
            raise ValueError("密码长度不能超过 72 字节")
        return v


# 返回给前端的用户信息（不含密码）
class UserOut(BaseModel):
    id: int
    username: str
    role: Role
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # 优先通过对象的属性读取值


# 登录成功返回的 token 和用户信息
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
