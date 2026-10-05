from sqlalchemy.orm import Session

from domain.entities.product import Product
from domain.repositories.product_repository import ProductRepositoryPort
from infrastructure.database.models.product_orm import ProductORM
from shared.infrastructure.sql_repository import SQLBaseRepository


class ProductRepository(SQLBaseRepository[Product, ProductORM], ProductRepositoryPort):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Product, ProductORM, "Producto")
