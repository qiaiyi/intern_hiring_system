"""Pydantic 模型统一出口：业务代码一律从 app.schemas 导入。

按业务实体拆分为 common / user / job / application 四个模块，
此处集中 re-export，路由层不需要关心具体拆分。
"""
from app.schemas.common import (
    ApplicationStatus,
    Page,
    PageParams,
    Role,
)
from app.schemas.user import Token, UserCreate, UserOut
from app.schemas.job import JobCreate, JobOut
from app.schemas.application import (
    ApplicationOut,
    ApplicationStatusUpdate,
    JobSummary,
    StudentSummary,
)

__all__ = [
    "Role",
    "ApplicationStatus",
    "Page",
    "PageParams",
    "UserCreate",
    "UserOut",
    "Token",
    "JobCreate",
    "JobOut",
    "JobSummary",
    "StudentSummary",
    "ApplicationOut",
    "ApplicationStatusUpdate",
]
