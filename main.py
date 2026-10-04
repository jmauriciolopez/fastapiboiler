from fastapi import FastAPI

from shared.infrastructure.exceptions import register_exception_handlers

app = FastAPI(title="Demo API", version="0.1.0")
register_exception_handlers(app)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def leer_raiz() -> dict[str, str]:
    return {"mensaje": "¡Hola, mundo!"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None) -> dict[str, int | str | None]:
    return {"item_id": item_id, "q": q}
