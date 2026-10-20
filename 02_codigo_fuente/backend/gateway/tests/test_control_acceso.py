"""Pruebas del control de acceso del gateway: token válido y permiso sobre el módulo de la ruta."""
from datetime import timedelta

import pytest

from src import mapa_rutas
from src.config import CORS_ORIGINS
from src.modulos import MODULO_ACCESOS, MODULO_FICHAS_EJEMPLARES, MODULO_PLANIFICACION

RUTAS_DE_ACCESOS = [
    ("GET", "/api/auth/usuarios"),
    ("POST", "/api/auth/usuarios"),
    ("PUT", "/api/auth/roles/2"),
    ("DELETE", "/api/auth/roles/2"),
    ("GET", "/api/auth/modulos"),
    ("GET", "/api/auth/permisos/matriz"),
    ("PUT", "/api/auth/permisos/2/1"),
]


# ---- Ruta pública ----

def test_login_pasa_sin_token(client_anonimo, servicio):
    response = client_anonimo.post("/api/auth/login", json={"correo": "a@b.com", "password": "x"})

    assert response.status_code == 200
    assert len(servicio.peticiones) == 1


def test_login_no_se_bloquea_por_un_token_invalido_adjunto(client_anonimo, servicio):
    response = client_anonimo.post("/api/auth/login", headers={"Authorization": "Bearer basura"})

    assert response.status_code == 200
    assert len(servicio.peticiones) == 1


# ---- 401: sin token o token inválido ----

@pytest.mark.parametrize("metodo,ruta", RUTAS_DE_ACCESOS)
def test_sin_token_401_y_no_llega_al_servicio(client_anonimo, servicio, metodo, ruta):
    response = client_anonimo.request(metodo, ruta)

    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.headers["www-authenticate"] == "Bearer"
    assert servicio.peticiones == []


@pytest.mark.parametrize(
    "authorization",
    ["Bearer", "Bearer ", "Basic abc123", "token-sin-esquema", "Bearer esto-no-es-un-jwt"],
)
def test_cabecera_authorization_mal_formada_401(client_anonimo, servicio, authorization):
    response = client_anonimo.get("/api/auth/usuarios", headers={"Authorization": authorization})

    assert response.status_code == 401
    assert servicio.peticiones == []


def test_token_firmado_con_otra_clave_401(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(modulos=[MODULO_ACCESOS], clave="otra-clave-distinta-de-la-del-gateway-123")

    response = client_anonimo.get("/api/auth/usuarios", headers=cabeceras(token))

    assert response.status_code == 401
    assert servicio.peticiones == []


def test_token_expirado_401(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(modulos=[MODULO_ACCESOS], expira_en=timedelta(seconds=-5))

    response = client_anonimo.get("/api/auth/usuarios", headers=cabeceras(token))

    assert response.status_code == 401
    assert servicio.peticiones == []


def test_token_sin_sub_401(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(modulos=[MODULO_ACCESOS], sub=None)

    assert client_anonimo.get("/api/auth/usuarios", headers=cabeceras(token)).status_code == 401
    assert servicio.peticiones == []


# ---- 403: token válido sin permiso ----

@pytest.mark.parametrize("metodo,ruta", RUTAS_DE_ACCESOS)
def test_rol_sin_permiso_sobre_accesos_403(client_anonimo, servicio, crear_token, cabeceras, metodo, ruta):
    token = crear_token(modulos=[MODULO_FICHAS_EJEMPLARES, MODULO_PLANIFICACION])

    response = client_anonimo.request(metodo, ruta, headers=cabeceras(token))

    assert response.status_code == 403
    assert "detail" in response.json()
    assert servicio.peticiones == []


def test_token_antiguo_sin_modulos_403(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token()  # sin claim "modulos"

    response = client_anonimo.get("/api/auth/usuarios", headers=cabeceras(token))

    assert response.status_code == 403
    assert servicio.peticiones == []


def test_modulos_vacio_403(client_anonimo, servicio, crear_token, cabeceras):
    response = client_anonimo.get("/api/auth/usuarios", headers=cabeceras(crear_token(modulos=[])))

    assert response.status_code == 403
    assert servicio.peticiones == []


# ---- Acceso permitido ----

@pytest.mark.parametrize("metodo,ruta", RUTAS_DE_ACCESOS)
def test_rol_con_permiso_sobre_accesos_pasa(client_anonimo, servicio, crear_token, cabeceras, metodo, ruta):
    token = crear_token(modulos=[MODULO_ACCESOS])

    response = client_anonimo.request(metodo, ruta, headers=cabeceras(token))

    assert response.status_code == 200
    assert len(servicio.peticiones) == 1


@pytest.mark.parametrize("metodo,ruta", RUTAS_DE_ACCESOS)
def test_administrador_pasa_sin_listar_modulos(client_anonimo, servicio, headers_admin, metodo, ruta):
    response = client_anonimo.request(metodo, ruta, headers=headers_admin)

    assert response.status_code == 200
    assert len(servicio.peticiones) == 1


def test_el_token_se_reenvia_al_servicio(client_anonimo, servicio, crear_token, cabeceras):
    headers = cabeceras(crear_token(modulos=[MODULO_ACCESOS]))

    client_anonimo.get("/api/auth/usuarios", headers=headers)

    assert servicio.ultima.headers["authorization"] == headers["Authorization"]


# ---- GET /roles: solo exige token válido ----

def test_listar_roles_sin_token_401(client_anonimo, servicio):
    assert client_anonimo.get("/api/auth/roles").status_code == 401
    assert servicio.peticiones == []


def test_listar_roles_con_token_sin_permisos_pasa(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(modulos=[])

    response = client_anonimo.get("/api/auth/roles", headers=cabeceras(token))

    assert response.status_code == 200
    assert len(servicio.peticiones) == 1


def test_listar_roles_con_token_invalido_401(client_anonimo, servicio):
    response = client_anonimo.get("/api/auth/roles", headers={"Authorization": "Bearer basura"})

    assert response.status_code == 401
    assert servicio.peticiones == []


@pytest.mark.parametrize("metodo", ["POST", "PUT", "PATCH", "DELETE"])
def test_modificar_roles_si_exige_permiso_de_accesos(client_anonimo, servicio, crear_token, cabeceras, metodo):
    token = crear_token(modulos=[])

    response = client_anonimo.request(metodo, "/api/auth/roles/2", headers=cabeceras(token))

    assert response.status_code == 403
    assert servicio.peticiones == []


def test_no_se_puede_usar_roles_para_llegar_a_otra_ruta(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(modulos=[])

    response = client_anonimo.get("/api/auth/roles/%2e%2e/usuarios", headers=cabeceras(token))

    assert response.status_code == 403
    assert servicio.peticiones == []


# ---- Orden de validaciones ----

def test_path_traversal_sin_token_responde_401_antes_que_400(client_anonimo, servicio):
    response = client_anonimo.get("/api/auth/%2e%2e/admin")

    assert response.status_code == 401
    assert servicio.peticiones == []


def test_path_traversal_con_permiso_sigue_respondiendo_400(client_anonimo, servicio, headers_admin):
    response = client_anonimo.get("/api/auth/%2e%2e/admin", headers=headers_admin)

    assert response.status_code == 400
    assert servicio.peticiones == []


def test_ruta_sin_mapear_se_rechaza_incluso_al_administrador(client_anonimo, servicio, headers_admin, monkeypatch):
    # Si una ruta no está en el mapa, el gateway no la deja pasar (falla cerrado)
    monkeypatch.setattr(mapa_rutas, "MAPA_MODULOS", {})

    response = client_anonimo.get("/api/auth/usuarios", headers=headers_admin)

    assert response.status_code == 403
    assert servicio.peticiones == []


# ---- CORS y otras rutas del gateway ----

def test_el_preflight_cors_no_exige_token(client_anonimo, servicio):
    response = client_anonimo.options(
        "/api/auth/usuarios",
        headers={
            "Origin": CORS_ORIGINS[0],
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert servicio.peticiones == []


def test_health_check_no_exige_token(client_anonimo):
    assert client_anonimo.get("/").status_code == 200
