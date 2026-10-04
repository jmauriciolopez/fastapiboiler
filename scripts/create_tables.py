import os

from sqlalchemy import create_engine

from infrastructure.database.models.role_orm import RoleORM
from shared.infrastructure.database import Base, _normalize_database_url


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL debe configurarse antes de crear las tablas.")

    engine = create_engine(_normalize_database_url(database_url), pool_pre_ping=True)
    try:
        Base.metadata.create_all(bind=engine, tables=[RoleORM.__table__])
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
