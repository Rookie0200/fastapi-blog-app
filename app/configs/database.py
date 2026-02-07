from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from configs.config import DATABASE_URL

DATABASE_URL = "sqlite:///./blog.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # required for SQLite
)

# engine = create_engin(DATABASE_URL)

sessionLocal = sessionmaker(autocommit=False, autoflush=False,bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    with sessionLocal() as db:
        yield db
