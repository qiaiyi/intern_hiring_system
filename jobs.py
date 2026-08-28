from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db_session
from models import Job, User
from schemas import JobCreate, JobOut, Page, PageParams
from dependencies import get_current_user, require_role
from pagination import paginate, build_page

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# 发布岗位（仅 HR）
@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role("hr"))
):
    job = Job(
        title=job_data.title,
        description=job_data.description,
        requirements=job_data.requirements,
        hr_id=current_user.id,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job

# 获取岗位列表（所有人可看，支持分页）
@router.get("", response_model=Page[JobOut])
async def list_jobs(
    params: PageParams = Depends(),
    db_session: AsyncSession = Depends(get_db_session)
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
    await db_session.commit()
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
    await db_session.commit()
    return None  # 204 响应无内容