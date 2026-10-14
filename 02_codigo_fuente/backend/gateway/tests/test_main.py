import httpx
from fastapi.testclient import TestClient

from src.config import CORS_ORIGINS
from src.main import app

ORIGEN_PERMITIDO = CORS_ORIGINS[0]


def test_health_check_responde_ok(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "operando correctamente" in response.json()["message"]


def test_lifespan_crea_y_cierra_el_cliente_http():
    with TestClient(app):
        cliente = app.state.http_client
        assert isinstance(cliente, httpx.AsyncClient)
        assert not cliente.is_closed

    assert cliente.is_closed


def test_cors_preflight_desde_origen_permitido(client):
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": ORIGEN_PERMITIDO,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGEN_PERMITIDO
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_preflight_desde_origen_no_permitido_es_rechazado(client):
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://sitio-malicioso.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_agrega_cabecera_en_respuesta_del_proxy(client):
    response = client.get("/api/auth/roles", headers={"Origin": ORIGEN_PERMITIDO})

    assert response.headers["access-control-allow-origin"] == ORIGEN_PERMITIDO


def test_el_preflight_no_llega_al_servicio(client, servicio):
    client.options(
        "/api/auth/usuarios",
        headers={"Origin": ORIGEN_PERMITIDO, "Access-Control-Request-Method": "GET"},
    )

    assert servicio.peticiones == []
