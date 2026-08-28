from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import DATABASE_URL, SQL_ECHO

engine = create_async_engine(DATABASE_URL, echo=SQL_ECHO)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

async def get_db_session():
    async with AsyncSessionLocal() as db_session:
        yield db_session