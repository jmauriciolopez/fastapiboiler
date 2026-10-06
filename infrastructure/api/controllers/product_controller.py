from uuid import UUID

from domain.entities.product import Product
from infrastructure.api.dependencies import get_product_service
from infrastructure.api.schemas.product_schemas import (
    ProductCreate,
    ProductPatch,
    ProductResponse,
    ProductUpdate,
)
from shared.infrastructure.generic_controller import create_generic_router


def update_product(product_id: int | UUID, payload: ProductUpdate) -> Product:
    if not isinstance(product_id, UUID):
        raise TypeError("El ID de un producto debe ser UUID.")
    return Product(id=product_id, name=payload.name)

def patch_product(
    product_id: int | UUID,
    current: Product,
    payload: ProductPatch,
) -> Product:
    if not isinstance(product_id, UUID):
        raise TypeError("El ID de un producto debe ser UUID.")
    return Product(
        id=product_id,
        name=payload.name if "name" in payload.model_fields_set else current.name,
    )


router = create_generic_router(
    service_provider=get_product_service,
    request_schema=ProductCreate,
    entity_factory=lambda payload: Product(name=payload.name),
    update_schema=ProductUpdate,
    update_factory=update_product,
    resource_name="Producto",
    response_schema=ProductResponse,
    entity_id_type=UUID,
    prefix="/products",
    tags=["Products"],
    patch_schema=ProductPatch,
    patch_factory=patch_product,
)
