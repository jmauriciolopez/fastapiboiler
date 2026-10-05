import os
from collections.abc import Callable, Generator
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


load_dotenv()


@lru_cache
def _get_session_factory(database_url: str) -> Callable[[], Session]:
    normalized_url = normalize_database_url(database_url)
    engine = create_engine(normalized_url, pool_pre_ping=True)
    return sessionmaker(autoflush=False, bind=engine)


def normalize_database_url(database_url: str) -> str:
    """Traduce una URL de SQLAlchemy al driver psycopg cuando usa PostgreSQL."""
    url = make_url(database_url)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    return url.render_as_string(hide_password=False)


def get_db() -> Generator[Session, None, None]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL debe configurarse para usar la base de datos.")

    db = _get_session_factory(database_url)()
    try:
        yield db
    finally:
        db.close()
