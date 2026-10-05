from application.ports.logger import LoggerPort
from domain.entities.product import Product
from domain.repositories.product_repository import ProductRepositoryPort
from shared.application.base_service import BaseService


class ProductService(BaseService[Product]):
    def __init__(self, repository: ProductRepositoryPort, logger: LoggerPort) -> None:
        super().__init__(repository, logger)
