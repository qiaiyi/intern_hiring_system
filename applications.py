from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db_session
from models import Application, Job, User
from schemas import ApplicationOut, ApplicationStatusUpdate, Page, PageParams
from dependencies import get_current_user, require_role
from pagination import paginate, build_page

router = APIRouter(prefix="/api", tags=["applications"])

# 学生投递岗位（需登录且角色为学生）
@router.post("/jobs/{job_id}/apply", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def apply_job(
    job_id: int,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role("student"))
):
    # 检查岗位是否存在
    result = await db_session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # 检查是否已投递过
    existing = await db_session.execute(
        select(Application).where(
            Application.job_id == job_id,
            Application.student_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="你已投递过该岗位")

    application = Application(
        job_id=job_id,
        student_id=current_user.id,
        status="applied"
    )
    db_session.add(application)
    await db_session.commit()
    await db_session.refresh(application)
    return application

# 学生查看自己的投递记录（支持分页）
@router.get("/my/applications", response_model=Page[ApplicationOut])
async def my_applications(
    params: Annotated[PageParams, Query()],
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role("student")),
):
    stmt = (
        select(Application)
        .where(Application.student_id == current_user.id)
        .order_by(Application.created_at.desc())
    )
    applications, total = await paginate(db_session, stmt, params)
    return build_page(applications, total, params)

# HR 查看某个岗位的投递列表（仅该岗位发布者，支持分页）
@router.get("/jobs/{job_id}/applications", response_model=Page[ApplicationOut])
async def list_job_applications(
    job_id: int,
    params: Annotated[PageParams, Query()],
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role("hr")),
):
    # 确认岗位存在且属于当前 HR
    job_result = await db_session.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.hr_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能查看自己发布岗位的投递")

    stmt = (
        select(Application)
        .where(Application.job_id == job_id)
        .order_by(Application.created_at.desc())
    )
    applications, total = await paginate(db_session, stmt, params)
    return build_page(applications, total, params)

# HR 更新投递状态
@router.put("/applications/{application_id}", response_model=ApplicationOut)
async def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role("hr"))
):
    result = await db_session.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="投递记录不存在")

    # 校验该投递对应的岗位是否属于当前 HR
    job_result = await db_session.execute(select(Job).where(Job.id == application.job_id))
    job = job_result.scalar_one_or_none()
    if not job or job.hr_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能修改自己发布岗位的投递状态")

    # 【重构】状态合法性已由 ApplicationStatus 枚举在 schema 层校验（非法值返回 422），
    # 这里无需再手动比对白名单，直接写入枚举的字符串值
    application.status = status_data.status.value
    await db_session.commit()
    await db_session.refresh(application)
    return application