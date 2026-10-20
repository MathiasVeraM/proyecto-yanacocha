import os

# Configuración de pruebas: debe fijarse antes de importar la app (el gateway exige SECRET_KEY)
CLAVE_PRUEBAS = "clave-solo-para-pruebas-con-longitud-suficiente"
os.environ.setdefault("SECRET_KEY", CLAVE_PRUEBAS)
os.environ.setdefault("ALGORITHM", "HS256")

from datetime import datetime, timedelta, timezone

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient

from src.config import ALGORITHM, SECRET_KEY
from src.main import app
from src.proxy import get_http_client

ID_ROL_ADMIN = 1
ID_ROL_USUARIO = 2


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
def crear_token():
    """Fábrica de tokens firmados como lo hace el servicio de accesos."""

    def _crear(
        id_rol=ID_ROL_USUARIO,
        modulos=None,
        sub="user@test.com",
        clave=SECRET_KEY,
        algoritmo=ALGORITHM,
        expira_en=timedelta(hours=1),
        **extra,
    ):
        payload = {"id_usuario": 99, "id_rol": id_rol, **extra}
        if sub is not None:
            payload["sub"] = sub
        if modulos is not None:
            payload["modulos"] = modulos
        payload["exp"] = datetime.now(timezone.utc) + expira_en
        return jwt.encode(payload, clave, algorithm=algoritmo)

    return _crear


@pytest.fixture
def cabeceras():
    """Convierte un token en la cabecera Authorization."""
    return lambda token: {"Authorization": f"Bearer {token}"}


@pytest.fixture
def headers_admin(crear_token, cabeceras):
    # El administrador no necesita listar módulos: pasa siempre
    return cabeceras(crear_token(id_rol=ID_ROL_ADMIN))


@pytest.fixture
def mock_http(servicio):
    async def cliente_simulado():
        async with httpx.AsyncClient(transport=httpx.MockTransport(servicio)) as cliente:
            yield cliente

    app.dependency_overrides[get_http_client] = cliente_simulado
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def servicio():
    return ServicioSimulado()


@pytest.fixture
def client_anonimo(mock_http):
    """Cliente sin credenciales, para probar el control de acceso."""
    return TestClient(app)


@pytest.fixture
def client(mock_http, headers_admin):
    """Cliente autenticado como administrador: las pruebas de reenvío no se ocupan de permisos."""
    return TestClient(app, headers=headers_admin)
