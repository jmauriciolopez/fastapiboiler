import os
from collections.abc import Generator
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()
load_dotenv()


@lru_cache
def _get_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url, pool_pre_ping=True)
    return sessionmaker(autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL debe configurarse para usar la base de datos.")

    db = _get_session_factory(database_url)()
    try:
        yield db
    finally:
        db.close()
