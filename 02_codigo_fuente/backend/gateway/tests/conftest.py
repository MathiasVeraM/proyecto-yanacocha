import httpx
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.proxy import get_http_client


class ServicioSimulado:
    """Reemplaza al microservicio real: registra lo que recibe y responde lo que se le configure."""

    def __init__(self):
        self.peticiones: list[httpx.Request] = []
        self.respuesta = httpx.Response(200, json={"ok": True})
        self.error: Exception | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        if self.error:
            raise self.error
        return self.respuesta

    @property
    def ultima(self) -> httpx.Request:
        return self.peticiones[-1]


@pytest.fixture
def servicio():
    return ServicioSimulado()


@pytest.fixture
def client(servicio):
    async def cliente_simulado():
        async with httpx.AsyncClient(transport=httpx.MockTransport(servicio)) as cliente:
            yield cliente

    app.dependency_overrides[get_http_client] = cliente_simulado
    yield TestClient(app)
    app.dependency_overrides.clear()
