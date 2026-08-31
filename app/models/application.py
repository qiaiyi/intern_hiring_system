from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.db.base import Base


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
