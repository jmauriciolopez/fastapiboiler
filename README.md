# Demo API

API REST en desarrollo con FastAPI, organizada con una base de arquitectura hexagonal. El proyecto contiene contratos genéricos para repositorios y servicios, pero todavía no incluye entidades ni endpoints CRUD de negocio. La sección [Crear una entidad y exponer sus endpoints](#crear-una-entidad-y-exponer-sus-endpoints) muestra un ejemplo ilustrativo; no agrega esa entidad al proyecto.

## Requisitos

- Python 3.12 o superior.
- pip.

## Instalación

Desde la carpeta raíz del proyecto, crea y activa un entorno virtual en PowerShell:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

Instala las dependencias:

```powershell
python -m pip install -r requirements.txt
```

## Ejecutar la API

```powershell
uvicorn main:app --reload
```

La API estará disponible en <http://127.0.0.1:8000>. La documentación interactiva de Swagger UI está en <http://127.0.0.1:8000/docs> y la especificación OpenAPI en <http://127.0.0.1:8000/openapi.json>.

### Rutas disponibles

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/health` | Comprueba que la API está activa. |
| `GET` | `/` | Ruta de ejemplo. |
| `GET` | `/items/{item_id}?q=texto` | Ruta de ejemplo; no usa una entidad ni una base de datos. |

## Estructura actual

```text
main.py
shared/
  application/
    base_service.py
  domain/
    base_repository.py
    exceptions.py
  infrastructure/
    database.py
    exceptions.py
    generic_controller.py
    sql_repository.py
tests/
  test_api.py
requirements.txt
```

- **Dominio:** contrato genérico `BaseRepository` y excepciones de dominio.
- **Aplicación:** `BaseService` delega las operaciones a un repositorio.
- **Infraestructura:** configuración de sesiones SQLAlchemy, implementación base del repositorio SQL, fábrica de routers y adaptación de excepciones de dominio a respuestas HTTP.
- **Composición:** `main.py` crea la aplicación y registra los manejadores de excepciones.

El router genérico no está montado en `main.py`: para usarlo hacen falta un esquema de entrada, una fábrica de entidad y una implementación de repositorio. Esos elementos se definirán cuando se agregue el primer dominio de negocio.

## Crear una entidad y exponer sus endpoints

El siguiente ejemplo muestra cómo agregar una entidad `Product`. Los archivos y el código son una guía: todavía no forman parte del proyecto. Mantén el modelo de dominio independiente de FastAPI y SQLAlchemy, y conecta las capas mediante el servicio y los adaptadores.

### 1. Crear la estructura de la funcionalidad

Una opción es organizar los componentes propios de la entidad por capa:

```text
products/
  domain/
    entities/
      product.py
  application/
    schemas/
      product_schemas.py
  infrastructure/
    persistence/
      product_orm.py
    http/
      product_controller.py
```

Agrega `__init__.py` a las carpetas si quieres declararlas explícitamente como paquetes Python.

### 2. Definir la entidad de dominio

En `products/domain/entities/product.py`, define el objeto que representa el concepto del negocio. No debe importar FastAPI, Pydantic ni SQLAlchemy:

```python
from dataclasses import dataclass


@dataclass
class Product:
    name: str
    price: float
    id: int | None = None
```

El campo `id` permite que el adaptador SQL convierta filas existentes a objetos de dominio. Ajusta los campos y reglas a las necesidades reales del negocio.

### 3. Crear esquemas de entrada y salida

En `products/application/schemas/product_schemas.py`, define los contratos HTTP con Pydantic:

```python
from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    price: float


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
```

El cliente no envía `id` al crear un producto; la base de datos lo genera. El esquema de respuesta sí lo incluye.

### 4. Mapear la entidad a SQLAlchemy

En `products/infrastructure/persistence/product_orm.py`, define la tabla usando el `Base` compartido:

```python
from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database import Base


class ProductORM(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    price: Mapped[float] = mapped_column(Float)
```

El `SQLBaseRepository` existente convierte entre las columnas del modelo ORM y el modelo de dominio. Por eso los nombres y campos del dominio deben ser compatibles con las columnas mapeadas.

### 5. Conectar el servicio y exponer las rutas

Para SQL, crea el servicio y su repositorio a partir de la sesión de cada solicitud. En `products/infrastructure/http/product_controller.py`:

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from products.application.schemas.product_schemas import ProductCreate, ProductResponse
from products.domain.entities.product import Product
from products.infrastructure.persistence.product_orm import ProductORM
from shared.application.base_service import BaseService
from shared.infrastructure.database import get_db
from shared.infrastructure.sql_repository import SQLBaseRepository

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_service(db: Session = Depends(get_db)) -> BaseService[Product]:
    repository = SQLBaseRepository(
        db=db,
        domain_model=Product,
        orm_model=ProductORM,
        resource_name="Producto",
    )
    return BaseService(repository)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    service: BaseService[Product] = Depends(get_product_service),
) -> Product:
    product = Product(name=payload.name, price=payload.price)
    return service.create(product)


@router.get("/", response_model=list[ProductResponse])
def list_products(
    service: BaseService[Product] = Depends(get_product_service),
) -> list[Product]:
    return service.list_all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    service: BaseService[Product] = Depends(get_product_service),
) -> Product | None:
    return service.get_by_id(product_id)
```

`get_db()` cierra la sesión al terminar la solicitud. La ruta `GET /products/{product_id}` produce una respuesta 404 cuando el repositorio lanza `EntityNotFoundException`, porque el manejador ya está registrado en `main.py`.

Monta el router en `main.py`:

```python
from products.infrastructure.http.product_controller import router as products_router

app.include_router(products_router, prefix="/api/v1")
```

Coloca el `include_router` después de crear `app` y registrar los manejadores. Con ese prefijo, quedan disponibles:

| Método | Ruta | Resultado |
| --- | --- | --- |
| `POST` | `/api/v1/products/` | Crea un producto y responde `201`. |
| `GET` | `/api/v1/products/` | Lista los productos. |
| `GET` | `/api/v1/products/{product_id}` | Obtiene un producto o responde `404`. |

Ejemplo de creación:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/products/ `
  -ContentType "application/json" `
  -Body '{"name":"Teclado","price":49.90}'
```

La documentación interactiva en `/docs` mostrará las nuevas rutas y los esquemas Pydantic.

> **Nota sobre `create_generic_router`:** actualmente recibe una instancia concreta de `BaseService` y solo crea las rutas `POST`, `GET` por ID y `GET` de colección; no implementa actualización ni eliminación. No construyas allí un servicio SQL con una sesión global o de larga duración: las sesiones SQLAlchemy no deben compartirse entre solicitudes. Para el adaptador SQL, el controlador del ejemplo crea el servicio con `Depends(get_db)` por solicitud. El router genérico puede utilizarse cuando la creación del servicio y el ciclo de vida del repositorio sean seguros para el contexto donde se monta.

## Base de datos

La API de ejemplo puede ejecutarse sin base de datos. La dependencia `get_db()` necesita que `DATABASE_URL` esté configurada antes de usarla; el proyecto no incluye una URL con credenciales por defecto ni crea tablas automáticamente.

Por ejemplo, para usar SQLite en PowerShell:

```powershell
$env:DATABASE_URL = "sqlite:///./app.db"
```

La sesión solo se crea cuando se solicita `get_db()`. Para usar el ejemplo de `Product`, configura una URL SQLAlchemy válida en `DATABASE_URL` y crea la tabla antes de llamar a sus endpoints. El proyecto no incluye migraciones ni crea tablas automáticamente; para desarrollo se puede crear un script de inicialización que importe `ProductORM` y ejecute `Base.metadata.create_all(engine)`. Para producción, utiliza una herramienta de migraciones como Alembic. Para PostgreSQL también se debe instalar el controlador correspondiente. No guardes credenciales reales en el código ni en archivos versionados.

## Pruebas

```powershell
python -m pytest -q
```

Las pruebas cubren las rutas de ejemplo, el endpoint de salud, el manejo de errores, los contratos genéricos y la validación del esquema del router.

## Estado actual

La entidad `Product` y sus rutas de ejemplo de esta guía no están implementadas. La base actual tampoco incluye esquemas específicos, routers CRUD conectados a la aplicación, migraciones ni configuración de una base de datos concreta. Al agregar la primera funcionalidad, implementa sus archivos por capa, configura la base de datos y añade pruebas para sus rutas y casos de uso.
