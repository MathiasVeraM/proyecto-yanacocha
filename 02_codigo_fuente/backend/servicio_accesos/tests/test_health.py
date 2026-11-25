from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from src.database import get_db
from src.main import app


def _sesion_sin_conexion():
    sesion = MagicMock()
    sesion.execute.side_effect = OperationalError(
        "SELECT 1", {}, Exception("password=clave-que-no-debe-salir host=10.0.0.5")
    )
    return sesion


def test_health_responde_sin_token(client):
    anonimo = TestClient(app)

    respuesta = anonimo.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_health_ready_responde_sin_token(client):
    anonimo = TestClient(app)

    respuesta = anonimo.get("/health/ready")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ready"}


def test_health_no_consulta_la_base_de_datos(client):
    sesion = MagicMock()
    app.dependency_overrides[get_db] = lambda: sesion

    TestClient(app).get("/health")

    sesion.execute.assert_not_called()


def test_health_ready_hace_una_consulta_trivial(client):
    sesion = MagicMock()
    app.dependency_overrides[get_db] = lambda: sesion

    respuesta = TestClient(app).get("/health/ready")

    assert respuesta.status_code == 200
    sesion.execute.assert_called_once()
    assert str(sesion.execute.call_args.args[0]) == "SELECT 1"


def test_health_ready_devuelve_503_si_la_base_no_responde(client):
    app.dependency_overrides[get_db] = _sesion_sin_conexion

    respuesta = TestClient(app).get("/health/ready")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "unavailable"}


def test_health_ready_no_expone_detalles_del_error(client):
    app.dependency_overrides[get_db] = _sesion_sin_conexion

    respuesta = TestClient(app).get("/health/ready")

    assert "clave-que-no-debe-salir" not in respuesta.text
    assert "10.0.0.5" not in respuesta.text


def test_health_solo_acepta_get(client):
    anonimo = TestClient(app)

    assert anonimo.post("/health").status_code == 405
    assert anonimo.delete("/health/ready").status_code == 405
