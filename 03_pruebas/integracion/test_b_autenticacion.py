"""b) Autenticación y módulos: login, tokens inválidos, módulos no permitidos y rutas no mapeadas."""
import os
import time

import jwt
import pytest

from ayudas import DOMINIO_CORREOS, crear_cliente, exigir


# ---------- Login ----------

def test_login_correcto_devuelve_un_token_con_el_rol_y_los_modulos(api_anonimo, usuarios):
    veterinaria = usuarios["veterinaria"]

    datos = exigir(
        api_anonimo.post("/api/auth/login", json={"correo": veterinaria.correo, "password": veterinaria.password})
    )

    assert datos["token_type"] == "bearer"
    payload = jwt.decode(datos["access_token"], options={"verify_signature": False})
    assert payload["sub"] == veterinaria.correo
    assert payload["id_usuario"] == veterinaria.id_usuario
    assert payload["id_rol"] == veterinaria.id_rol
    assert "servicio-gestion-animal" in payload["modulos"]
    assert "servicio-actividades" not in payload["modulos"]


def test_login_con_contrasena_incorrecta_401(api_anonimo, usuarios):
    respuesta = api_anonimo.post(
        "/api/auth/login", json={"correo": usuarios["manejo"].correo, "password": "incorrecta-123"}
    )

    assert respuesta.status_code == 401


def test_login_con_correo_inexistente_da_el_mismo_error_que_una_contrasena_mala(api_anonimo, usuarios):
    inexistente = api_anonimo.post(
        "/api/auth/login", json={"correo": f"nadie@{DOMINIO_CORREOS}", "password": "incorrecta-123"}
    )
    mala = api_anonimo.post(
        "/api/auth/login", json={"correo": usuarios["manejo"].correo, "password": "incorrecta-123"}
    )

    assert inexistente.status_code == mala.status_code == 401
    assert inexistente.json() == mala.json()


def test_login_con_correo_mal_formado_422(api_anonimo):
    respuesta = api_anonimo.post("/api/auth/login", json={"correo": "no-es-un-correo", "password": "x"})

    assert respuesta.status_code == 422


def test_login_de_un_usuario_desactivado_403(api_anonimo, api_admin, usuario_temporal):
    usuario = usuario_temporal()
    exigir(api_admin.patch(f"/api/auth/usuarios/{usuario.id_usuario}/desactivar"))

    respuesta = api_anonimo.post("/api/auth/login", json={"correo": usuario.correo, "password": usuario.password})

    assert respuesta.status_code == 403


# ---------- Token ausente, inválido o vencido ----------

RUTAS_PROTEGIDAS = ["/api/auth/usuarios", "/api/animales", "/api/actividades", "/api/actividades/calendario"]


@pytest.mark.parametrize("ruta", RUTAS_PROTEGIDAS)
def test_sin_token_401(api_anonimo, ruta):
    assert api_anonimo.get(ruta).status_code == 401


@pytest.mark.parametrize("ruta", RUTAS_PROTEGIDAS)
def test_token_basura_401(ruta):
    with crear_cliente("esto-no-es-un-jwt") as cliente:
        assert cliente.get(ruta).status_code == 401


def test_token_firmado_con_otra_clave_401():
    falso = jwt.encode(
        {"sub": f"intruso@{DOMINIO_CORREOS}", "id_usuario": 1, "id_rol": 1, "modulos": [], "exp": int(time.time()) + 3600},
        "una-clave-que-no-es-la-del-sistema-123456",
        algorithm="HS256",
    )
    with crear_cliente(falso) as cliente:
        assert cliente.get("/api/auth/usuarios").status_code == 401


@pytest.mark.skipif(not os.environ.get("SECRET_KEY"), reason="Se necesita SECRET_KEY para fabricar un token vencido")
def test_token_vencido_401(usuarios):
    manejo = usuarios["manejo"]
    vencido = jwt.encode(
        {
            "sub": manejo.correo,
            "id_usuario": manejo.id_usuario,
            "id_rol": manejo.id_rol,
            "modulos": ["servicio-actividades"],
            "exp": int(time.time()) - 60,
        },
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )
    with crear_cliente(vencido) as cliente:
        assert cliente.get("/api/actividades").status_code == 401


@pytest.mark.parametrize("cabecera", ["Basic dXN1YXJpbzpjbGF2ZQ==", "Bearer", "token-sin-esquema"])
def test_cabecera_authorization_mal_formada_401(api_anonimo, cabecera):
    assert api_anonimo.get("/api/actividades", headers={"Authorization": cabecera}).status_code == 401


# ---------- Módulos ----------

def test_voluntario_no_accede_al_modulo_de_fichas_403(api_voluntario):
    respuesta = api_voluntario.get("/api/animales")

    assert respuesta.status_code == 403
    assert "módulo" in respuesta.json()["detail"]


def test_veterinaria_no_accede_al_modulo_de_planificacion_403(api_veterinaria):
    assert api_veterinaria.get("/api/actividades").status_code == 403
    assert api_veterinaria.get("/api/actividades/calendario").status_code == 403


@pytest.mark.parametrize("cliente", ["api_veterinaria", "api_manejo", "api_voluntario"])
def test_solo_el_administrador_accede_al_modulo_de_accesos_403(request, cliente):
    assert request.getfixturevalue(cliente).get("/api/auth/usuarios").status_code == 403


def test_roles_solo_necesita_token_valido(api_anonimo, api_voluntario, api_veterinaria):
    assert api_anonimo.get("/api/auth/roles").status_code == 401
    assert api_voluntario.get("/api/auth/roles").status_code == 200
    assert api_veterinaria.get("/api/auth/roles").status_code == 200


def test_el_administrador_accede_a_todos_los_modulos(api_admin):
    assert api_admin.get("/api/auth/usuarios").status_code == 200
    assert api_admin.get("/api/animales").status_code == 200
    assert api_admin.get("/api/actividades").status_code == 200


# ---------- Rutas que el gateway no conoce ----------

@pytest.mark.parametrize(
    "ruta", ["/api/desconocido", "/api/estadisticas/resumen", "/api/authx", "/api/actividadesx", "/admin"]
)
def test_ruta_no_mapeada_no_se_reenvia(api_admin, ruta):
    # Ni siquiera el administrador llega a un servicio por una ruta que el mapa no contempla
    assert api_admin.get(ruta).status_code in (403, 404)


def test_path_traversal_se_rechaza_400(api_admin):
    # Doble codificación: así el cliente HTTP no la normaliza antes de enviarla
    assert api_admin.get("/api/auth/%252e%252e/%252e%252e/usuarios").status_code == 400
    assert api_admin.get("/api/actividades/%252e%252e/usuarios").status_code == 400


def test_el_health_de_los_servicios_no_se_alcanza_por_el_proxy(api_anonimo):
    # /health de cada servicio es interno: por el proxy sigue exigiendo token
    assert api_anonimo.get("/api/actividades/health").status_code == 401
    assert api_anonimo.get("/api/animales/health").status_code == 401
