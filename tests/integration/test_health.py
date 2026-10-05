"""Pruebas de integración del cableado completo de la aplicación."""

from fastapi.testclient import TestClient

from main import app


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# def test_existing_demo_routes_remain_available() -> None:
#     client = TestClient(app)

#     assert client.get("/").json() == {"mensaje": "¡Hola, mundo!"}
#     assert client.get("/items/7?q=test").json() == {"item_id": 7, "q": "test"}
