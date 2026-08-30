from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, UniqueConstraint
from datetime import datetime
from database import Base
from sqlalchemy import func
from sqlalchemy.orm import relationship



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

# 在原有 User 模型下方添加

class Job(Base):
    __tablename__ = "job"
    # 【新增】同一 HR 不能发布同名岗位：数据库唯一约束兜底并发场景，
    # 与投递去重（uq_application_job_student）思路一致
    __table_args__ = (
        UniqueConstraint("hr_id", "title", name="uq_job_hr_title"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    requirements = Column(String(1000), nullable=False)
    hr_id = Column(Integer, ForeignKey("user.id"), nullable=False)  # 发布者
    created_at = Column(DateTime, server_default=func.now())

    # 关系（供 JobOut / ApplicationOut 嵌套时预加载）
    hr = relationship("User")
    applications = relationship("Application", back_populates="job")


class Application(Base):
    __tablename__ = "application"
    # 【新增】同一学生对同一岗位只能投递一次，由数据库唯一约束兜底并发场景
    __table_args__ = (
        UniqueConstraint("job_id", "student_id", name="uq_application_job_student"),
    )

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    status = Column(String(20), default="applied")  # applied / screening / interview / offer / rejected
    created_at = Column(DateTime, server_default=func.now())

    # 关系（供 ApplicationOut 嵌套显示岗位与投递人信息）
    job = relationship("Job", back_populates="applications")
    student = relationship("User")