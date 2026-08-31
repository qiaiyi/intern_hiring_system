from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import DATABASE_URL, SQL_ECHO
from app.db.base import Base

engine = create_async_engine(DATABASE_URL, echo=SQL_ECHO)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db_session():
    async with AsyncSessionLocal() as db_session:
        yield db_session