"""通用分页工具：复用 SQLAlchemy 的 select 语句，避免每个列表接口重复写 count + offset/limit。"""
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import PageParams


async def paginate(db_session: AsyncSession, stmt, params: PageParams):
    """对任意 select 语句执行分页查询。

    返回 (items, total)：items 为当前页的 ORM 对象列表，total 为满足条件的总行数。
    这里假设传入的 stmt 是一个只 select 实体（未含聚合/分组）的查询语句，
    直接对其子查询计数即可得到总数。
    """
    # 总数：对原查询取 count
    total = (
        await db_session.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()

    # 当前页数据
    result = await db_session.execute(
        stmt.offset(params.offset).limit(params.page_size)
    )
    items = list(result.scalars().all())
    return items, total


def build_page(items, total: int, params: PageParams):
    """把分页查询结果组装成统一的 Page 响应字典。"""
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "pages": ceil(total / params.page_size) if total else 0,
    }
