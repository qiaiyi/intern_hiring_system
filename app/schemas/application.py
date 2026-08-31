"""投递相关 Pydantic 模型：投递返回、状态更新。"""
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional

from app.schemas.common import ApplicationStatus


# 【新增】投递列表里嵌套展示的岗位 / 学生摘要，避免只返回裸 ID
class JobSummary(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)


class StudentSummary(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationOut(BaseModel):
    id: int
    status: ApplicationStatus
    created_at: datetime
    job: JobSummary           # 学生侧：投的是哪个岗位
    student: StudentSummary   # HR 侧：投递人是谁

    model_config = ConfigDict(from_attributes=True)


# HR 更新投递状态
class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus  # 允许 screening / interview / offer / rejected

    # 【校验】applied 是投递时的初始态，不允许 HR 通过更新接口改回
    @field_validator("status")
    @classmethod
    def not_applied(cls, v: ApplicationStatus) -> ApplicationStatus:
        if v == ApplicationStatus.applied:
            raise ValueError("不能将状态改回 applied")
        return v
