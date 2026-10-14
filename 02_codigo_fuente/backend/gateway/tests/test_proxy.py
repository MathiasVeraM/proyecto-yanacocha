"""Pruebas de la lógica común del proxy, reutilizada por todos los routers del gateway."""
import asyncio
from types import SimpleNamespace

import pytest
from starlette.requests import Request

from src.config import PROXY_TIMEOUT_SECONDS
from src.proxy import (
    CABECERAS_EXCLUIDAS_PETICION,
    CABECERAS_EXCLUIDAS_RESPUESTA,
    construir_cabeceras_peticion,
    crear_cliente_http,
    es_ruta_segura,
    filtrar_cabeceras,
    get_http_client,
)


def crear_request(headers: dict[str, str] | None = None, client=("10.0.0.5", 1234), scheme="http"):
    scope = {
        "type": "http",
        "method": "GET",
        "scheme": scheme,
        "server": ("gateway", 8000),
        "path": "/api/auth/usuarios",
        "query_string": b"",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": client,
    }
    return Request(scope)


# ---- es_ruta_segura ----

@pytest.mark.parametrize(
    "path",
    [
        "",
        "login",
        "usuarios",
        "usuarios/5",
        "usuarios/5/desactivar",
        "archivo.v2.json",
        "carpeta/...",
        "nombre..con..puntos",
    ],
)
def test_rutas_normales_son_seguras(path):
    assert es_ruta_segura(path)


@pytest.mark.parametrize(
    "path",
    [
        "..",
        "../admin",
        "usuarios/../../admin",
        "usuarios/..",
        "%2e%2e/admin",
        "%2E%2E/admin",
        "%252e%252e/admin",
        ".%2e/admin",
        "..\\admin",
        "usuarios%2f..%2fadmin",
    ],
)
def test_rutas_con_traversal_no_son_seguras(path):
    assert not es_ruta_segura(path)


# ---- filtrar_cabeceras ----

def test_filtrar_cabeceras_quita_las_excluidas_sin_importar_mayusculas():
    cabeceras = [("Connection", "keep-alive"), ("Authorization", "Bearer x"), ("HOST", "gateway")]

    resultado = filtrar_cabeceras(cabeceras, CABECERAS_EXCLUIDAS_PETICION)

    assert resultado == [("Authorization", "Bearer x")]


def test_filtrar_cabeceras_conserva_cabeceras_repetidas():
    cabeceras = [("set-cookie", "a=1"), ("set-cookie", "b=2"), ("transfer-encoding", "chunked")]

    resultado = filtrar_cabeceras(cabeceras, CABECERAS_EXCLUIDAS_RESPUESTA)

    assert resultado == [("set-cookie", "a=1"), ("set-cookie", "b=2")]


@pytest.mark.parametrize("cabecera", ["host", "content-length", "connection", "transfer-encoding", "upgrade"])
def test_cabeceras_excluidas_en_peticion(cabecera):
    assert cabecera in CABECERAS_EXCLUIDAS_PETICION


@pytest.mark.parametrize("cabecera", ["content-encoding", "content-length", "connection", "transfer-encoding"])
def test_cabeceras_excluidas_en_respuesta(cabecera):
    assert cabecera in CABECERAS_EXCLUIDAS_RESPUESTA


# ---- construir_cabeceras_peticion ----

def test_agrega_x_forwarded_for_con_la_ip_del_cliente():
    cabeceras = dict(construir_cabeceras_peticion(crear_request()))

    assert cabeceras["x-forwarded-for"] == "10.0.0.5"
    assert cabeceras["x-forwarded-proto"] == "http"


def test_encadena_x_forwarded_for_existente():
    request = crear_request(headers={"X-Forwarded-For": "200.1.1.1"})

    cabeceras = construir_cabeceras_peticion(request)

    assert [v for k, v in cabeceras if k == "x-forwarded-for"] == ["200.1.1.1, 10.0.0.5"]


def test_reemplaza_x_forwarded_proto_enviado_por_el_cliente():
    request = crear_request(headers={"X-Forwarded-Proto": "falso"}, scheme="https")

    cabeceras = construir_cabeceras_peticion(request)

    assert [v for k, v in cabeceras if k == "x-forwarded-proto"] == ["https"]


def test_cliente_sin_ip_se_marca_como_desconocido():
    cabeceras = dict(construir_cabeceras_peticion(crear_request(client=None)))

    assert cabeceras["x-forwarded-for"] == "desconocido"


def test_no_reenvia_host_ni_hop_by_hop():
    request = crear_request(headers={"Host": "gateway", "Connection": "close", "Authorization": "Bearer t"})

    nombres = [k for k, _ in construir_cabeceras_peticion(request)]

    assert "host" not in nombres
    assert "connection" not in nombres
    assert "authorization" in nombres


# ---- cliente HTTP ----

def test_crear_cliente_http_usa_el_timeout_configurado():
    cliente = crear_cliente_http()

    assert cliente.timeout.read == PROXY_TIMEOUT_SECONDS
    assert cliente.timeout.connect == PROXY_TIMEOUT_SECONDS
    asyncio.run(cliente.aclose())


def test_get_http_client_devuelve_el_cliente_de_la_app():
    cliente = object()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(http_client=cliente)))

    assert get_http_client(request) is cliente
