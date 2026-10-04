from fastapi import FastAPI

from infrastructure.api.controllers.role_controller import router as roles_router
from shared.infrastructure.exceptions import register_exception_handlers

app = FastAPI(title="Demo API", version="0.1.0")
register_exception_handlers(app)
app.include_router(roles_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def leer_raiz() -> dict[str, str]:
    return {"mensaje": "¡Hola, mundo!"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None) -> dict[str, int | str | None]:
    return {"item_id": item_id, "q": q}
