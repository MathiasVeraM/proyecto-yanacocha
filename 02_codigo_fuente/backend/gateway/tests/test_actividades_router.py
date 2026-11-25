"""Pruebas del proxy de /api/actividades/* con un microservicio simulado."""

import httpx
import pytest
from fastapi.testclient import TestClient

from src.config import ACTIVIDADES_SERVICE_URL
from src.main import app
from src.modulos import MODULO_ACCESOS, MODULO_PLANIFICACION
from src.permisos_rol import ID_ROL_MANEJO_ANIMAL
from src.rutas.actividades_router import URL_DESTINO


@pytest.fixture
def client(mock_http, crear_token, cabeceras):
    # Manejo de Animales puede usar todos los métodos de planificación: estas pruebas
    # revisan el reenvío, no los permisos por rol (ver test_permisos_rol.py)
    token = crear_token(id_rol=ID_ROL_MANEJO_ANIMAL, modulos=[MODULO_PLANIFICACION])
    return TestClient(app, headers=cabeceras(token))


@pytest.mark.parametrize("metodo", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_reenvia_cada_metodo_permitido(client, servicio, metodo):
    respuesta = client.request(metodo, "/api/actividades/1/completar")

    assert respuesta.status_code == 200
    assert servicio.ultima.method == metodo
    assert str(servicio.ultima.url) == f"{URL_DESTINO}/1/completar"


@pytest.mark.parametrize("metodo", ["GET", "POST"])
def test_raiz_del_prefijo_se_reenvia_sin_barra_final(client, servicio, metodo):
    client.request(metodo, "/api/actividades")

    assert str(servicio.ultima.url) == f"{ACTIVIDADES_SERVICE_URL}/api/actividades"


def test_url_destino_apunta_al_servicio_de_actividades():
    assert URL_DESTINO == f"{ACTIVIDADES_SERVICE_URL}/api/actividades"


def test_reenvia_cuerpo_y_query_params(client, servicio):
    solicitud = {"id_dieta": 4, "fecha_hasta": "2026-03-30"}

    client.post("/api/actividades/tomas/generar?origen=manual", json=solicitud)

    assert servicio.ultima.url.query == b"origen=manual"
    assert servicio.ultima.content == httpx.Request("POST", "http://x", json=solicitud).read()


def test_reenvia_el_token_de_autorizacion(client, servicio):
    client.get("/api/actividades")

    assert servicio.ultima.headers["authorization"] == client.headers["Authorization"]


def test_respeta_estado_y_respuesta_del_servicio(client, servicio):
    servicio.respuesta = httpx.Response(409, json={"detail": "Actividad duplicada"})

    respuesta = client.post("/api/actividades/dietas")

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "Actividad duplicada"}


def test_path_traversal_no_llega_al_servicio(client, servicio):
    respuesta = client.get("/api/actividades/%2e%2e/api/auth/usuarios")

    assert respuesta.status_code == 400
    assert servicio.peticiones == []


@pytest.mark.parametrize(
    "ruta",
    ["/api/actividades", "/api/actividades/dietas"],
)
def test_sin_token_devuelve_401_y_no_reenvia(client_anonimo, servicio, ruta):
    respuesta = client_anonimo.get(ruta)

    assert respuesta.status_code == 401
    assert servicio.peticiones == []


@pytest.mark.parametrize(
    "ruta",
    ["/api/actividades", "/api/actividades/1/completar"],
)
def test_token_sin_modulo_de_planificacion_devuelve_403(
    client_anonimo, servicio, crear_token, cabeceras, ruta
):
    token = crear_token(modulos=[MODULO_ACCESOS])

    respuesta = client_anonimo.get(ruta, headers=cabeceras(token))

    assert respuesta.status_code == 403
    assert servicio.peticiones == []


def test_token_con_modulo_de_planificacion_pasa_al_servicio(
    client_anonimo, servicio, crear_token, cabeceras
):
    token = crear_token(id_rol=ID_ROL_MANEJO_ANIMAL, modulos=[MODULO_PLANIFICACION])

    respuesta = client_anonimo.post(
        "/api/actividades/tomas/generar",
        headers=cabeceras(token),
        json={"id_dieta": 3},
    )

    assert respuesta.status_code == 200
    assert len(servicio.peticiones) == 1
