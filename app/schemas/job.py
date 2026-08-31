"""岗位相关 Pydantic 模型：发布、更新与返回。"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class JobCreate(BaseModel):
    # 【问题19】上限与 models.py 列宽对齐（title: 100，description/requirements: 1000），必填字段同时补 min_length=1 拦截空串
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    requirements: str = Field(min_length=1, max_length=1000)


class JobOut(BaseModel):
    id: int
    title: str
    description: str
    requirements: str
    hr_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
