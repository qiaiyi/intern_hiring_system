from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db_session
from app.models import Job, User
from app.schemas import JobCreate, JobOut, Page, PageParams
from app.api.dependencies import get_current_user, require_role
from app.utils.pagination import paginate, build_page

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# 发布岗位（仅 HR）
@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role("hr"))
):
    # 【新增】发布前防重：同一 HR 不能发布同名岗位。
    # 唯一约束 (hr_id, title) 是并发场景的最终兜底，这里先给常规重复提交一个友好提示。
    existing = await db_session.execute(
        select(Job).where(
            Job.hr_id == current_user.id,
            Job.title == job_data.title,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="你已发布过同名岗位")

    job = Job(
        title=job_data.title,
        description=job_data.description,
        requirements=job_data.requirements,
        hr_id=current_user.id,
    )
    db_session.add(job)
    # 【新增】并发下两个请求都通过上面的查询后，第二个 INSERT 会撞唯一约束
    # uq_job_hr_title 抛 IntegrityError，这里捕获并回滚，避免 500，同时保证不重复入库。
    try:
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail="你已发布过同名岗位")
    await db_session.refresh(job)
    return job

# 获取岗位列表（所有人可看，支持分页）
@router.get("", response_model=Page[JobOut])
async def list_jobs(
    params: Annotated[PageParams, Query()],
    db_session: AsyncSession = Depends(get_db_session),
):
    stmt = select(Job).order_by(Job.created_at.desc())
    jobs, total = await paginate(db_session, stmt, params)
    return build_page(jobs, total, params)

# 获取岗位详情
@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return job

# 更新岗位（仅发布者 HR）
@router.put("/{job_id}", response_model=JobOut)
async def update_job(
    job_id: int,
    job_data: JobCreate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role("hr"))
):
    result = await db_session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.hr_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能修改自己发布的岗位")

    job.title = job_data.title
    job.description = job_data.description
    job.requirements = job_data.requirements
    # 【修复】改名为同名岗位时 INSERT/UPDATE 撞 uq_job_hr_title 唯一约束
    # 抛 IntegrityError，捕获并回滚返回 400，避免 500（与 create_job 的兜底一致）。
    try:
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail="你已发布过同名岗位")
    await db_session.refresh(job)
    return job

# 删除岗位（仅发布者 HR）
@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role("hr"))
):
    result = await db_session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.hr_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己发布的岗位")

    await db_session.delete(job)
    # 【修复】岗位已有投递记录时，application.job_id 外键（默认 RESTRICT）
    # 会阻止删除并抛 IntegrityError，此前未捕获导致 500。
    # 这里捕获并回滚，返回 400 提示先处理投递记录（不做级联删除，避免静默丢数据）。
    try:
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(
            status_code=400,
            detail="该岗位已有投递记录，无法删除",
        )
    return None  # 204 响应无内容