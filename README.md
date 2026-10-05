# Demo API

API REST en desarrollo con FastAPI, organizada con una base de arquitectura hexagonal. Incluye las entidades `Role` y `User`, con endpoints CRUD y borrado lógico. Los contratos genéricos permiten agregar otros recursos siguiendo las capas de dominio, aplicación e infraestructura.

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

## Ejecutar con Docker

Construye la imagen desde la raíz del proyecto:

```powershell
docker build -t demo-api .
```

La aplicación requiere que `DATABASE_URL` apunte a una base de datos PostgreSQL accesible desde el contenedor y que `JWT_SECRET_KEY` esté configurada. En PowerShell, establece las variables y arranca el contenedor:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://..."
$env:JWT_SECRET_KEY = "..."
docker run --rm -p 8000:8000 -e DATABASE_URL -e JWT_SECRET_KEY demo-api
```

La API quedará disponible en <http://localhost:8000>. Si PostgreSQL corre en el host Windows, usa `host.docker.internal` como host en `DATABASE_URL`, no `localhost`. Las tablas deben estar creadas antes de usar la API; para inicializarlas con la misma configuración, ejecuta `docker run --rm -e DATABASE_URL demo-api python -m scripts.create_tables`. La imagen incluye un health check contra `/health`. No copies secretos al contexto de build; los archivos `.env` están excluidos por `.dockerignore`.

## Configurar PostgreSQL

La API lee `DATABASE_URL` desde el entorno o desde un archivo `.env` en la raíz. Para PostgreSQL con Psycopg 3, configura `DATABASE_URL` con una URL SQLAlchemy que use el driver `postgresql+psycopg` y los datos de conexión de tu entorno. Por ejemplo, el valor debe tener este formato:

```dotenv
DATABASE_URL=postgresql+psycopg://...
```

El paquete `psycopg[binary]` ya está declarado en `requirements.txt`. También se aceptan URLs con esquema `postgres://` o `postgresql://`; la configuración las normaliza al driver `postgresql+psycopg`. Mantén las credenciales reales fuera del código y no agregues el archivo `.env` al control de versiones.

La autenticación JWT usa el encabezado `Authorization: Bearer <token>` y requiere `JWT_SECRET_KEY`. Por separado, las rutas que se protejan con `Depends(get_valid_api_key)` requieren `X-API-Key: <clave>` y `API_KEY`. La dependencia `get_valid_api_key` está disponible en `infrastructure.api.security`; actualmente no está aplicada a ninguna ruta. No se exige que ambas credenciales se envíen juntas.

Los errores HTTP se responden con `application/problem+json`, siguiendo RFC 9457 (Problem Details). El objeto incluye `type`, `title`, `status`, `detail` e `instance`; `code` es una extensión estable de la API. Los errores de validación agregan una extensión `errors` con ubicación y tipo, sin incluir los valores recibidos. Las excepciones inesperadas se registran en el servidor y responden con un detalle genérico.

Una vez creada la base de datos, inicializa las tablas y luego inicia la API:

```powershell
python -m scripts.create_tables
uvicorn main:app --reload
```

El script crea las tablas `roles`, `users` y `user_roles` si no existen; no aplica migraciones ni modifica tablas existentes.

Si ya tienes una base de datos creada con el esquema anterior, aplica una migración antes de desplegar esta versión: renombra `roles.rol` a `roles.name`, elimina el índice único global anterior de `users.email` y crea los índices únicos parciales `uq_users_active_email_ci` y `uq_roles_active_name_ci`. `create_tables` no transforma datos ni actualiza índices existentes.

### Rutas disponibles

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/health` | Comprueba que la API está activa. |
| `POST` | `/api/v1/roles/` | Crea un rol y responde `201`. |
| `GET` | `/api/v1/roles/?limit=20&offset=0` | Lista roles activos con paginación. |
| `GET` | `/api/v1/roles/{role_id}` | Obtiene un rol o responde `404` si no existe. |
| `PUT` | `/api/v1/roles/{role_id}` | Actualiza el nombre del rol. |
| `DELETE` | `/api/v1/roles/{role_id}` | Marca el rol como eliminado; responde `204`. |
| `POST` | `/api/v1/users/` | Crea un usuario; recibe contraseña y la persiste como hash Argon2. |
| `GET` | `/api/v1/users/?limit=20&offset=0` | Lista usuarios activos con paginación. |
| `GET` | `/api/v1/users/{user_id}` | Obtiene un usuario y sus roles activos. |
| `PUT` | `/api/v1/users/{user_id}` | Actualiza el usuario, roles y opcionalmente su contraseña. |
| `DELETE` | `/api/v1/users/{user_id}` | Marca el usuario como eliminado; responde `204`. |

## Estructura actual

```text
main.py
domain/
  entities/
    role.py
    user.py
  exceptions/
    auth_exceptions.py
  repositories/
    role_repository.py
    user_repository.py
application/
  ports/
    password_hasher.py
    token_service.py
  services/
    auth_service.py
    role_service.py
    user_service.py
infrastructure/
  api/
    dependencies.py
    exceptions.py
    controllers/
      role_controller.py
      user_controller.py
    schemas/
      role_schemas.py
      user_schemas.py
  database/
    models/
      role_orm.py
      user_orm.py
    repositories/
      role_repository.py
      user_repository.py
  security/
    password_hasher.py
shared/
  application/
    base_service.py
  domain/
    entities.py
    exceptions.py
    pagination.py
    repository_port.py
  infrastructure/
    database.py
    exceptions.py
    generic_controller.py
    integrity_errors.py
    sql_repository.py
scripts/
  create_tables.py
tests/
  conftest.py
  fakes.py
  unit/
    test_base_service.py
    test_database.py
    test_entities.py
    test_exception_handlers.py
    test_generic_router.py
    test_integrity_errors.py
    test_password_hasher.py
    test_schemas.py
  integration/
    test_health.py
    test_roles_api.py
    test_users_api.py
requirements.txt
```

- **Dominio:** entidades, contrato genérico `RepositoryPort` y puertos especializados para `Role` y `User`. Los repositorios concretos declaran explícitamente el puerto que implementan.
- **Aplicación:** `RoleService` y `UserService` dependen de puertos del dominio y reutilizan `BaseService`; `UserService` además aplica reglas de usuario y usa el puerto `PasswordHasher`.
- **Infraestructura:** configuración de sesiones SQLAlchemy, implementación base del repositorio SQL que centraliza `commit`/`rollback`, fábrica de routers y adaptación de excepciones a respuestas HTTP (dominio y 500 genérico).
- **Roles:** el controlador usa `create_generic_router` con `RoleService`; el servicio depende de `RoleRepositoryPort`, y el proveedor de infraestructura conecta el puerto con `RoleRepository` por solicitud.
- **Composición:** `main.py` crea la aplicación, registra los manejadores de excepciones y monta los routers `/api/v1/roles` y `/api/v1/users`.

El controlador de roles reutiliza `create_generic_router`. La fábrica recibe el proveedor de servicio, los esquemas HTTP y el tipo de ID, para exponer operaciones comunes sin compartir una sesión SQLAlchemy entre solicitudes. La selección del adaptador concreto se hace fuera del controlador, en `infrastructure/api/dependencies.py`.

`SQLBaseRepository` realiza las escrituras a través de un límite transaccional común: si `commit` falla, revierte la sesión. Las restricciones únicas conocidas se declaran en `_integrity_conflict_messages` y se traducen a `DomainConflictException`; cualquier otro `IntegrityError` se repropaga. Para adaptar el mapeo de una entidad con relaciones, se puede sobrescribir `_to_orm`; `UserRepository` lo hace para asociar los roles y sigue reutilizando `save` del repositorio base.

## Paginación, actualización y eliminación lógica

Los endpoints de colección aceptan `limit` (entre 1 y 100; valor predeterminado 20) y `offset` (desde 0; valor predeterminado 0). La respuesta incluye la página y el total de registros activos:

```json
{
  "items": [{"id": "UUID", "name": "admin"}],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

Ejemplo de página siguiente:

```powershell
curl.exe "http://127.0.0.1:8000/api/v1/roles/?limit=10&offset=10"
```

`PUT /api/v1/roles/{role_id}` reemplaza los campos editables del rol. El cuerpo es:

```json
{"name": "editor"}
```

`DELETE /api/v1/roles/{role_id}` hace una eliminación lógica: conserva la fila y marca `deleted=true`. Los roles eliminados no aparecen en el listado ni se pueden consultar o actualizar; esas operaciones responden 404.

### Respuestas de error

Los errores de dominio y los fallos no mapeados usan el mismo sobre JSON:

```json
{
  "error": {
    "code": "not_found",
    "message": "Rol con ID ... no existe."
  }
}
```

| Origen | HTTP | `code` |
| --- | --- | --- |
| Recurso inexistente o eliminado | 404 | `not_found` |
| Validación de reglas de dominio | 422 | `domain_validation_error` |
| Conflicto (unicidad clasificada) | 409 | `conflict` |
| Credenciales inválidas | 401 | `invalid_credentials` |
| Otro error de dominio | 400 | `domain_error` |
| Excepción no mapeada | 500 | `internal_error` |

`AuthException` hereda de `DomainException`, y su manejador específico se registra en `infrastructure/api/exceptions.py` sobre los genéricos de `shared/infrastructure/exceptions.py`: responde `401` con la cabecera `WWW-Authenticate: Bearer`. Así el dominio no conoce códigos HTTP y el kernel compartido no depende del dominio de la aplicación.

Las violaciones de unicidad de `uq_users_active_email_ci` y `uq_roles_active_name_ci` se convierten en `DomainConflictException` (409). Un `IntegrityError` de FK, `NOT NULL` u otro índice no se clasifica: sale como 500 con `code` `internal_error` y el mensaje fijo `"Error interno del servidor."`, sin detalle SQL. El traceback queda en el log del servidor.

Los errores de validación del cuerpo y parámetros HTTP continúan usando el formato estándar de FastAPI; no usan este sobre.

## Entidad Role

`Role` contiene `id` (UUID generado en el dominio) y `name` (texto obligatorio de 1 a 80 caracteres); hereda los campos de auditoría y eliminación lógica de `AuditableEntity`, que no se exponen en el esquema HTTP. Los nombres de rol son únicos sin distinguir mayúsculas entre roles activos; al eliminar un rol lógicamente, su nombre puede reutilizarse.

Los archivos que la implementan son:

| Capa | Archivo | Responsabilidad |
| --- | --- | --- |
| Dominio | `domain/entities/role.py` | Entidad Python `Role`, basada en la clase auditable existente. |
| Infraestructura/API | `infrastructure/api/schemas/role_schemas.py` | Validación de entrada y respuesta HTTP. |
| Infraestructura/BD | `infrastructure/database/models/role_orm.py` | Tabla SQLAlchemy `roles`. |
| Infraestructura/API | `infrastructure/api/controllers/role_controller.py` | Router CRUD genérico; el servicio se inyecta desde `dependencies.py`. |

Ejemplo para crear un rol:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/roles/ `
  -ContentType "application/json" `
  -Body '{"name":"admin"}'
```

Para consultar o actualizar un rol, usa su UUID, devuelto al crearlo. `GET /api/v1/roles/` devuelve una página de resultados; `DELETE /api/v1/roles/{role_id}` lo elimina lógicamente. Los nombres duplicados responden `409`. La documentación interactiva en `/docs` muestra las rutas y los esquemas.

Para agregar otra entidad, sigue el mismo patrón por capas: entidad de dominio, esquemas Pydantic, modelo SQLAlchemy con un campo booleano `deleted`, proveedor de servicio por solicitud y registro del router genérico. La paginación y operaciones genéricas dependen de que el repositorio respete el contrato de `RepositoryPort`.

## Base de datos

La ruta `/health` funciona sin base de datos. Para los endpoints de roles y usuarios, configura `DATABASE_URL` antes de inicializar el esquema y ejecutar la API; no hay URL con credenciales por defecto. Para opciones de configuración de PostgreSQL, consulta [Configurar PostgreSQL](#configurar-postgresql).

Como alternativa, puedes usar SQLite en PowerShell:

```powershell
$env:DATABASE_URL = "sqlite:///./app.db"
```

Con `DATABASE_URL` configurada, crea las tablas `roles`, `users` y `user_roles`:

```powershell
python -m scripts.create_tables
```

`get_db()` abre y cierra una sesión por solicitud. Si las tablas ya existían antes de agregar los campos de usuario, actualízalas mediante una migración (por ejemplo, Alembic); `create_tables` no altera tablas existentes.

## Entidad User

La API recibe `password` al crear o actualizar, lo transforma con Argon2 en el servidor y lo persiste únicamente en la columna `password_hash`. El campo de dominio se llama `hashed_password` y las respuestas nunca exponen ni `password` ni `hashed_password`. Los usuarios nuevos comienzan en estado `pending`; los estados disponibles son `pending`, `active`, `inactive` y `blocked`. Cada usuario puede asociarse a varios roles existentes y activos mediante `role_ids`. Los emails activos son únicos; si una cuenta se elimina lógicamente, su email puede reutilizarse.

Ejemplo de creación:

```json
{
  "username": "Ada Lovelace",
  "email": "ada@example.com",
  "phone": "+1-555-0100",
  "password": "una-clave-segura",
  "role_ids": ["UUID-de-un-rol"]
}
```

Si se omite `role_ids`, el usuario se crea sin roles. En `PUT`, envía un nuevo `password` para cambiar la credencial; si se omite o es `null`, se conserva el hash actual. Los roles inexistentes o eliminados generan `404`; los correos duplicados, `409`.

## Pruebas

```powershell
python -m pytest -q
```

Las pruebas están separadas por tipo: `tests/unit/` no toca la base de datos (entidades, esquemas, `BaseService`, router genérico, clasificador de integridad, manejadores HTTP —incluido el 500 JSON— y configuración de la base) y `tests/integration/` levanta la aplicación completa contra SQLite en memoria (salud, roles, usuarios y hash de contraseña).

`tests/fakes.py` expone un único `InMemoryRepository` genérico que respeta el contrato de `RepositoryPort`. `tests/conftest.py` aporta las fixtures compartidas `engine`, `session_factory` y `client`; esta última sustituye `get_db` por la base en memoria y restaura los overrides al terminar cada prueba.

Para ejecutar solo una suite:

```powershell
python -m pytest tests/unit -q
python -m pytest tests/integration -q
```

## Lint y tipos

Ruff y mypy están en `requirements.txt`. Desde la raíz:

```powershell
ruff check .
mypy .
```

O ambos a la vez con el entorno de hatch:

```powershell
hatch run check
```

Mypy corre en modo `strict` con el plugin de Pydantic. Que el proyecto pase la comprobación es parte del contrato: las clases base genéricas (`RepositoryPort`, `SQLBaseRepository`, `BaseService`) existen en parte para que el tipado se propague sin `Any` sueltos.

## Estado actual

Las entidades `Role` y `User` exponen creación, lectura paginada, actualización completa y eliminación lógica. La capa de autenticación está en curso: `AuthService.login` y los puertos `PasswordHasher` y `TokenServicePort` ya existen, pero todavía no hay implementación de `TokenServicePort`, endpoint de login ni pruebas del servicio. Las migraciones de base de datos tampoco están implementadas.
