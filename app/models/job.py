from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.db.base import Base


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
