from typing import Protocol

from domain.entities.product import Product
from shared.domain.repository_port import RepositoryPort


class ProductRepositoryPort(RepositoryPort[Product], Protocol):
    pass
