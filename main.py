from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from infrastructure.api.controllers.auth_controller import router as auth_router
from infrastructure.api.controllers.product_controller import router as products_router
from infrastructure.api.controllers.role_controller import router as roles_router
from infrastructure.api.controllers.user_controller import router as users_router
from infrastructure.api.exceptions import register_api_exception_handlers
from shared.infrastructure.persistence.database import get_engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    engine = get_engine()
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(title="Demo API", version="0.1.0", lifespan=lifespan)
register_api_exception_handlers(app)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
