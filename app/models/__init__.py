"""SQLAlchemy 模型按业务实体拆分，统一从 app.models 导入使用。

SQLAlchemy 的 relationship("User") 按类名字符串解析，
拆分后各模型类只要都被 import 进本包即可正常互相引用。
"""
from app.models.user import User
from app.models.job import Job
from app.models.application import Application

__all__ = ["User", "Job", "Application"]
