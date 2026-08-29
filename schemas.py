from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, Generic, TypeVar
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



# 注册请求体
class UserCreate(BaseModel):
    username: str
    password: str
    role: Role = Role.student
    name: Optional[str] = None   # 姓名（可选）
    email: Optional[str] = None  # 邮箱（可选）

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
        return v

# 登录请求体
class UserLogin(BaseModel):
    username: str
    password: str

# 返回给前端的用户信息（不含密码）
class UserOut(BaseModel):
    id: int
    username: str
    role: Role
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)#优先通过对象的属性（.属性名）而非字典键（['键名']）来读取值

# 登录成功返回的 token 和用户信息
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# 岗位相关
class JobCreate(BaseModel):
    title: str
    description: str
    requirements: str

class JobOut(BaseModel):
    id: int
    title: str
    description: str
    requirements: str
    hr_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
# 投递相关
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