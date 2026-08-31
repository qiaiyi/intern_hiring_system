"""Pydantic 模型公共部分：枚举与分页结构，各业务 schema 统一从这里引用。"""
from pydantic import BaseModel, field_validator
from typing import Generic, TypeVar
from enum import Enum

# 分页泛型
T = TypeVar("T")


class Role(str, Enum):
    student = "student"
    hr = "hr"


class ApplicationStatus(str, Enum):
    applied = "applied"
    screening = "screening"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"


# 【新增】分页查询参数：列表接口的公共查询参数，供 FastAPI 自动解析与校验
class PageParams(BaseModel):
    page: int = 1
    page_size: int = 10

    # 【校验】分页参数边界，非法值直接返回 422
    @field_validator("page")
    @classmethod
    def page_ge_1(cls, v: int) -> int:
        if v < 1:
            raise ValueError("page 必须 >= 1")
        return v

    @field_validator("page_size")
    @classmethod
    def page_size_range(cls, v: int) -> int:
        if v < 1:
            raise ValueError("page_size 必须 >= 1")
        if v > 100:
            raise ValueError("page_size 最大为 100")
        return v

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


# 【新增】分页响应结构：items 为当前页数据，其余为分页元信息
class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
