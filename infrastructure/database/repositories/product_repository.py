from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.product import Product
from domain.repositories.product_repository import ProductRepositoryPort
from infrastructure.database.models.product_orm import ProductORM
from shared.infrastructure.sql_repository import SQLBaseRepository


class ProductRepository(SQLBaseRepository[Product, ProductORM], ProductRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Product, ProductORM, "Producto")

    def _to_domain(self, orm_entity: ProductORM) -> Product:
        return Product(
            id=orm_entity.id,
            name=orm_entity.name,
            created_on=orm_entity.created_on,
            updated_on=orm_entity.updated_on,
            deleted=orm_entity.deleted,
        )

    def _to_orm(self, entity: Product) -> ProductORM:
        return ProductORM(
            id=entity.id,
            name=entity.name,
            created_on=entity.created_on,
            updated_on=entity.updated_on,
            deleted=entity.deleted,
        )
