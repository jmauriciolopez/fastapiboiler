# Demo API

API REST en desarrollo con FastAPI, organizada con una base de arquitectura hexagonal. Incluye la entidad `Role` y endpoints para crear, listar y consultar roles. Los contratos genéricos permiten agregar otros recursos siguiendo las capas de dominio, aplicación e infraestructura.

## Requisitos

- Python 3.12 o superior.
- pip.

## Instalación

Desde la carpeta raíz del proyecto, crea y activa un entorno virtual en PowerShell:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

Instala las dependencias de la API, pruebas y lint:

```powershell
python -m pip install -r requirements.txt
```

## Ejecutar la API

```powershell
uvicorn main:app --reload
```

La API estará disponible en <http://127.0.0.1:8000>. La documentación interactiva de Swagger UI está en <http://127.0.0.1:8000/docs> y la especificación OpenAPI en <http://127.0.0.1:8000/openapi.json>.

## Configurar PostgreSQL

La API lee `DATABASE_URL` desde el entorno o desde un archivo `.env` en la raíz. Para PostgreSQL con Psycopg 3, configura `DATABASE_URL` con una URL SQLAlchemy que use el driver `postgresql+psycopg` y los datos de conexión de tu entorno. Por ejemplo, el valor debe tener este formato:

```dotenv
DATABASE_URL=postgresql+psycopg://...
```

El paquete `psycopg[binary]` ya está declarado en `requirements.txt`. También se aceptan URLs con esquema `postgres://` o `postgresql://`; la configuración las normaliza al driver `postgresql+psycopg`. Mantén las credenciales reales fuera del código y no agregues el archivo `.env` al control de versiones.

Una vez creada la base de datos, inicializa la tabla de roles y luego inicia la API:

```powershell
python -m scripts.create_tables
uvicorn main:app --reload
```

El script crea la tabla `roles` si no existe; no aplica migraciones ni modifica tablas existentes.

### Rutas disponibles

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/health` | Comprueba que la API está activa. |
| `GET` | `/` | Ruta de ejemplo. |
| `GET` | `/items/{item_id}?q=texto` | Ruta de ejemplo; no usa una entidad ni una base de datos. |
| `POST` | `/api/v1/roles/` | Crea un rol y responde `201`. |
| `GET` | `/api/v1/roles/?limit=20&offset=0` | Lista roles activos con paginación. |
| `GET` | `/api/v1/roles/{role_id}` | Obtiene un rol o responde `404` si no existe. |
| `PUT` | `/api/v1/roles/{role_id}` | Actualiza el nombre (`rol`) del rol. |
| `DELETE` | `/api/v1/roles/{role_id}` | Marca el rol como eliminado; responde `204`. |

## Estructura actual

```text
main.py
domain/
  entities/
    role.py
infrastructure/
  api/
    controllers/
      role_controller.py
    schemas/
      role_schemas.py
  database/
    models/
      role_orm.py
shared/
  application/
    base_service.py
  domain/
    base_repository.py
    entities.py
    exceptions.py
  infrastructure/
    database.py
    exceptions.py
    generic_controller.py
    sql_repository.py
scripts/
  create_tables.py
tests/
  test_api.py
requirements.txt
```

- **Dominio:** contrato genérico `BaseRepository` y excepciones de dominio.
- **Aplicación:** `BaseService` delega las operaciones a un repositorio.
- **Infraestructura:** configuración de sesiones SQLAlchemy, implementación base del repositorio SQL, fábrica de routers y adaptación de excepciones de dominio a respuestas HTTP.
- **Roles:** entidad en `domain/`, esquemas HTTP y adaptadores en `infrastructure/`; su controlador usa `create_generic_router` y provee el servicio/repositorio por solicitud.
- **Composición:** `main.py` crea la aplicación, registra los manejadores de excepciones y monta el router `/api/v1/roles`.

El controlador de roles reutiliza `create_generic_router`. La fábrica recibe el proveedor de servicio, los esquemas HTTP y el tipo de ID, para exponer operaciones comunes sin compartir una sesión SQLAlchemy entre solicitudes.

## Paginación, actualización y eliminación lógica

Los endpoints de colección aceptan `limit` (entre 1 y 100; valor predeterminado 20) y `offset` (desde 0; valor predeterminado 0). La respuesta incluye la página y el total de registros activos:

```json
{
  "items": [{"id": "UUID", "rol": "admin"}],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

Ejemplo de página siguiente:

```powershell
curl.exe "http://127.0.0.1:8000/api/v1/roles/?limit=10&offset=10"
```

`PUT /api/v1/roles/{role_id}` reemplaza los campos editables del rol. El cuerpo actual es:

```json
{"rol": "editor"}
```

`DELETE /api/v1/roles/{role_id}` hace una eliminación lógica: conserva la fila y marca `deleted=true`. Los roles eliminados no aparecen en el listado ni se pueden consultar o actualizar; esas operaciones responden 404.

### Respuestas de errores de dominio

Los errores de dominio usan un formato JSON uniforme:

```json
{
  "error": {
    "code": "not_found",
    "message": "Rol con ID ... no existe."
  }
}
```

Los códigos HTTP son 404 para recursos inexistentes o eliminados, 422 para errores de validación del dominio, 409 para conflictos y 400 para otros errores de dominio. Los errores de validación del cuerpo y parámetros HTTP continúan usando el formato estándar de FastAPI.

## Entidad Role

`Role` es la primera entidad concreta del proyecto. Contiene `id` (UUID generado en el dominio) y `rol` (texto obligatorio de 1 a 80 caracteres); hereda los campos de auditoría y eliminación lógica de `AuditableEntity`, que no se exponen en el esquema HTTP.

Los archivos que la implementan son:

| Capa | Archivo | Responsabilidad |
| --- | --- | --- |
| Dominio | `domain/entities/role.py` | Entidad Python `Role`, basada en la clase auditable existente. |
| Infraestructura/API | `infrastructure/api/schemas/role_schemas.py` | Validación de entrada y respuesta HTTP. |
| Infraestructura/BD | `infrastructure/database/models/role_orm.py` | Tabla SQLAlchemy `roles`. |
| Infraestructura/API | `infrastructure/api/controllers/role_controller.py` | Endpoints, servicio y repositorio por solicitud. |

Ejemplo para crear un rol:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/roles/ `
  -ContentType "application/json" `
  -Body '{"rol":"admin"}'
```

Para consultar o actualizar un rol, usa su UUID, devuelto al crearlo. `GET /api/v1/roles/` devuelve una página de resultados; `DELETE /api/v1/roles/{role_id}` lo elimina lógicamente. La documentación interactiva en `/docs` muestra las rutas y los esquemas.

Para agregar otra entidad, sigue el mismo patrón por capas: entidad de dominio, esquemas Pydantic, modelo SQLAlchemy con un campo booleano `deleted`, proveedor de servicio por solicitud y registro del router genérico. La paginación y operaciones genéricas dependen de que el repositorio respete el contrato de `BaseRepository`.

## Base de datos

Las rutas `/health`, `/` e `/items` funcionan sin base de datos. Para endpoints de roles, configura `DATABASE_URL` antes de inicializar el esquema y ejecutar la API; no hay URL con credenciales por defecto. Para opciones de configuración de PostgreSQL, consulta [Configurar PostgreSQL](#configurar-postgresql).

Como alternativa, puedes usar SQLite en PowerShell:

```powershell
$env:DATABASE_URL = "sqlite:///./app.db"
```

Con `DATABASE_URL` configurada, crea la tabla `roles`:

```powershell
python -m scripts.create_tables
```

`get_db()` abre y cierra una sesión por solicitud. El esquema `roles` debe incluir los campos `deleted` y `updated_on` para soportar eliminación lógica y fecha de modificación. Si ya existía antes de esos campos, actualízalo mediante una migración (por ejemplo, Alembic); `create_tables` no altera tablas existentes.

## Pruebas

```powershell
python -m pytest -q
```

Las pruebas cubren las rutas de ejemplo, el endpoint de salud, el manejo de errores, la paginación, actualización y eliminación lógica, usando una base SQLite en memoria para las rutas de roles.

## Ruff

Ruff está incluido en `requirements.txt`. Para revisar el código Python desde la raíz:

```powershell
ruff check .
```

## Estado actual

La entidad `Role` expone creación, lectura paginada, actualización completa y eliminación lógica. Las migraciones de base de datos aún no están implementadas.
