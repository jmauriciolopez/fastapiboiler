from domain.entities.product import Product
from domain.repositories.product_repository import ProductRepositoryPort
from shared.application.base_service import BaseService
from shared.application.ports.logger import LoggerPort
from shared.application.unit_of_work import UnitOfWork


class ProductService(BaseService[Product]):
    def __init__(
        self,
        repository: ProductRepositoryPort,
        uow: UnitOfWork,
        logger: LoggerPort,
    ) -> None:
        super().__init__(repository, uow, logger)
