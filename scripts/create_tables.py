import os

from sqlalchemy import create_engine

from infrastructure.database.models.product_orm import ProductORM  # noqa: F401
from infrastructure.database.models.role_orm import RoleORM  # noqa: F401
from infrastructure.database.models.user_orm import UserORM  # noqa: F401
from shared.infrastructure.persistence.database import Base, normalize_database_url


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL debe configurarse antes de crear las tablas.")

    engine = create_engine(normalize_database_url(database_url), pool_pre_ping=True)
    try:
        Base.metadata.create_all(bind=engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
