from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase
# from core.config import DATABASE_URL

DATABASE_URL = "sqlite+aiosqlite:///./blog.db"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # required for SQLite
)

# engine = create_engin(DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
