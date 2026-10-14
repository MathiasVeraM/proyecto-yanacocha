"""Pruebas del reenvío de /api/auth/* al servicio de accesos (con el servicio simulado)."""
import gzip
import json

import httpx
import pytest

from src.rutas.accesos_router import URL_DESTINO


# ---- Reenvío de la petición ----

@pytest.mark.parametrize("metodo", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_reenvia_cada_metodo_permitido(client, servicio, metodo):
    response = client.request(metodo, "/api/auth/usuarios/5")

    assert response.status_code == 200
    assert servicio.ultima.method == metodo
    assert str(servicio.ultima.url) == f"{URL_DESTINO}/usuarios/5"


def test_metodo_no_permitido_no_llega_al_servicio(client, servicio):
    response = client.request("TRACE", "/api/auth/usuarios")

    assert response.status_code == 405
    assert servicio.peticiones == []


def test_reenvia_el_cuerpo_del_login(client, servicio):
    credenciales = {"correo": "admin@yanacocha.com", "password": "secreta"}

    client.post("/api/auth/login", json=credenciales)

    assert json.loads(servicio.ultima.content) == credenciales
    assert servicio.ultima.headers["content-type"] == "application/json"


def test_reenvia_query_params_incluyendo_repetidos(client, servicio):
    client.get("/api/auth/usuarios?activo=true&rol=1&rol=2")

    assert servicio.ultima.url.query == b"activo=true&rol=1&rol=2"


def test_sin_query_params_no_agrega_signo_de_interrogacion(client, servicio):
    client.get("/api/auth/roles")

    assert str(servicio.ultima.url) == f"{URL_DESTINO}/roles"


def test_reenvia_el_token_de_autorizacion(client, servicio):
    client.get("/api/auth/usuarios", headers={"Authorization": "Bearer token-de-prueba"})

    assert servicio.ultima.headers["authorization"] == "Bearer token-de-prueba"


def test_no_reenvia_el_host_del_gateway(client, servicio):
    client.get("/api/auth/roles")

    assert servicio.ultima.headers["host"] == servicio.ultima.url.netloc.decode()


def test_agrega_cabeceras_x_forwarded(client, servicio):
    client.get("/api/auth/roles", headers={"X-Forwarded-For": "190.1.1.1"})

    assert servicio.ultima.headers["x-forwarded-for"] == "190.1.1.1, testclient"
    assert servicio.ultima.headers["x-forwarded-proto"] == "http"


def test_ruta_raiz_del_prefijo(client, servicio):
    client.get("/api/auth/")

    assert str(servicio.ultima.url) == f"{URL_DESTINO}/"


# ---- Path traversal ----

@pytest.mark.parametrize(
    "ruta",
    [
        "/api/auth/%2e%2e/admin",
        "/api/auth/usuarios/%2e%2e/%2e%2e/docs",
        "/api/auth/%252e%252e/admin",
        "/api/auth/.%2e/admin",
    ],
)
def test_bloquea_path_traversal_sin_llamar_al_servicio(client, servicio, ruta):
    response = client.get(ruta)

    assert response.status_code == 400
    assert response.json() == {"detail": "Ruta no permitida"}
    assert servicio.peticiones == []


# ---- Respuesta del servicio ----

@pytest.mark.parametrize("codigo", [200, 201, 400, 401, 403, 404, 422, 500])
def test_respeta_el_codigo_de_estado_del_servicio(client, servicio, codigo):
    servicio.respuesta = httpx.Response(codigo, json={"detail": "respuesta del servicio"})

    response = client.get("/api/auth/usuarios")

    assert response.status_code == codigo
    assert response.json() == {"detail": "respuesta del servicio"}


def test_devuelve_el_cuerpo_y_content_type_del_servicio(client, servicio):
    usuarios = [{"id_usuario": 1, "nombre": "Jorge"}]
    servicio.respuesta = httpx.Response(200, json=usuarios)

    response = client.get("/api/auth/usuarios")

    assert response.json() == usuarios
    assert response.headers["content-type"] == "application/json"


def test_no_reenvia_cabeceras_hop_by_hop_de_la_respuesta(client, servicio):
    servicio.respuesta = httpx.Response(
        200,
        content=b"ok",
        headers={"Connection": "close", "Keep-Alive": "timeout=5", "X-Request-Id": "abc"},
    )

    response = client.get("/api/auth/roles")

    assert response.headers["x-request-id"] == "abc"
    assert "keep-alive" not in response.headers


def test_respuesta_comprimida_llega_descomprimida_y_sin_content_encoding(client, servicio):
    cuerpo = json.dumps({"ok": True}).encode()
    servicio.respuesta = httpx.Response(
        200,
        content=gzip.compress(cuerpo),
        headers={"Content-Encoding": "gzip", "Content-Type": "application/json"},
    )

    response = client.get("/api/auth/roles")

    assert "content-encoding" not in response.headers
    assert response.headers["content-length"] == str(len(cuerpo))
    assert response.json() == {"ok": True}


def test_conserva_cabeceras_set_cookie_repetidas(client, servicio):
    servicio.respuesta = httpx.Response(
        200,
        content=b"ok",
        headers=[("Set-Cookie", "a=1"), ("Set-Cookie", "b=2")],
    )

    response = client.get("/api/auth/roles")

    assert response.headers.get_list("set-cookie") == ["a=1", "b=2"]


# ---- Errores de conexión ----

def test_servicio_caido_devuelve_503(client, servicio):
    servicio.error = httpx.ConnectError("conexión rechazada")

    response = client.get("/api/auth/usuarios")

    assert response.status_code == 503
    assert response.json() == {"detail": "El servicio de accesos no está disponible"}


@pytest.mark.parametrize("error", [httpx.ReadTimeout("lento"), httpx.ConnectTimeout("lento")])
def test_servicio_lento_devuelve_504(client, servicio, error):
    servicio.error = error

    response = client.get("/api/auth/usuarios")

    assert response.status_code == 504
    assert response.json() == {"detail": "El servicio de accesos no respondió a tiempo"}


def test_otros_errores_de_red_devuelven_503(client, servicio):
    servicio.error = httpx.RemoteProtocolError("respuesta inválida")

    response = client.get("/api/auth/usuarios")

    assert response.status_code == 503
