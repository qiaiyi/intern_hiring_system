"""pytest 共享 fixture：为每个测试提供独立的 SQLite 数据库与 httpx 客户端。

说明：
- 使用文件型 SQLite（aiosqlite）替代 MySQL，测试无需真实数据库服务；
- 每个用例独立建库，保证用例间数据隔离；
- 通过 app.dependency_overrides 把 get_db_session 指向测试会话工厂，
  使被测接口在不改动业务代码的前提下使用测试数据库。
"""
import pytest_asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from main import app
from database import Base, get_db_session


@pytest_asyncio.fixture
async def client(tmp_path):
    """返回一个指向测试库的 httpx AsyncClient（ASGI 传输，无需启动真实服务）。"""
    db_file = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await engine.dispose()
