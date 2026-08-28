from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from datetime import datetime
from database import Base
from sqlalchemy import func



class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default="student")  # 学生和 HR 共用一张表
    created_at = Column(DateTime, server_default=func.now())

# 在原有 User 模型下方添加

class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    requirements = Column(String(1000), nullable=False)
    hr_id = Column(Integer, ForeignKey("user.id"), nullable=False)  # 发布者
    created_at = Column(DateTime, server_default=func.now())

    # 关系（可选，方便后续查询）
    # hr = relationship("User", backref="jobs")


class Application(Base):
    __tablename__ = "application"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    status = Column(String(20), default="applied")  # applied / screening / interview / offer / rejected
    created_at = Column(DateTime, server_default=func.now())