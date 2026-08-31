from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from sqlalchemy import func

from app.db.base import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default="student")  # 学生和 HR 共用一张表
    # 【新增】真实招聘系统基础字段：姓名、邮箱（可空，兼容已有数据）
    name = Column(String(80))
    email = Column(String(120))
    created_at = Column(DateTime, server_default=func.now())
