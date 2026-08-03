import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ponytail: SQLite default for zero-setup dev; swap DATABASE_URL to
# postgresql+psycopg://... for prod. async SQLAlchemy when the read load
# demands it, not before.
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///./aabdm.db"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
