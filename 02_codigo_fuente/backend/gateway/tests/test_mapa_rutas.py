"""Pruebas del mapa que relaciona cada ruta del gateway con su código de servicio."""
import pytest

from src import mapa_rutas
from src.mapa_rutas import NIVEL_MODULO, NIVEL_PUBLICA, NIVEL_TOKEN, resolver_regla
from src.modulos import (
    MODULO_ACCESOS,
    MODULO_ESTADISTICAS,
    MODULO_FICHAS_EJEMPLARES,
    MODULO_PLANIFICACION,
)


def test_codigos_de_servicio_coinciden_con_la_tabla_modulo():
    assert MODULO_FICHAS_EJEMPLARES == "servicio-gestion-animal"
    assert MODULO_PLANIFICACION == "servicio-actividades"
    assert MODULO_ESTADISTICAS == "servicio-estadisticas"
    assert MODULO_ACCESOS == "servicio-accesos"


# ---- Rutas públicas y de solo token ----

def test_login_es_publico():
    regla = resolver_regla("POST", "/api/auth/login")

    assert regla.nivel == NIVEL_PUBLICA


def test_login_con_barra_final_sigue_siendo_publico():
    assert resolver_regla("POST", "/api/auth/login/").nivel == NIVEL_PUBLICA


def test_listar_roles_solo_exige_token():
    regla = resolver_regla("GET", "/api/auth/roles")

    assert regla.nivel == NIVEL_TOKEN


def test_listar_roles_con_barra_final_solo_exige_token():
    assert resolver_regla("GET", "/api/auth/roles/").nivel == NIVEL_TOKEN


# ---- Rutas que exigen permiso sobre el módulo de accesos ----

@pytest.mark.parametrize(
    "metodo,ruta",
    [
        ("GET", "/api/auth/usuarios"),
        ("POST", "/api/auth/usuarios"),
        ("PUT", "/api/auth/usuarios/3"),
        ("PATCH", "/api/auth/usuarios/3/desactivar"),
        ("GET", "/api/auth/modulos"),
        ("POST", "/api/auth/modulos"),
        ("GET", "/api/auth/permisos/matriz"),
        ("PUT", "/api/auth/permisos/2/1"),
        ("DELETE", "/api/auth/permisos/2/1"),
        # Solo el GET de /roles es de token: el resto de métodos modifica roles
        ("POST", "/api/auth/roles"),
        ("PUT", "/api/auth/roles/2"),
        ("DELETE", "/api/auth/roles/2"),
        # Solo el POST del login es público
        ("GET", "/api/auth/login"),
        ("GET", "/api/auth"),
        ("GET", "/api/auth/"),
    ],
)
def test_rutas_de_accesos_exigen_el_modulo_de_accesos(metodo, ruta):
    regla = resolver_regla(metodo, ruta)

    assert regla.nivel == NIVEL_MODULO
    assert regla.codigo_servicio == MODULO_ACCESOS


@pytest.mark.parametrize(
    "ruta",
    ["/api/auth/roles/../usuarios", "/api/auth/login/../usuarios", "/api/auth/roles/2"],
)
def test_una_ruta_publica_no_se_cuela_con_segmentos_extra(ruta):
    # La comparación de rutas públicas es exacta, no por prefijo
    assert resolver_regla("GET", ruta).nivel == NIVEL_MODULO


# ---- Rutas sin mapear ----

@pytest.mark.parametrize("ruta", ["/api/otra", "/api/authx/usuarios", "/", "/api"])
def test_ruta_sin_mapear_devuelve_none(ruta):
    assert resolver_regla("GET", ruta) is None


def test_el_prefijo_se_compara_por_segmentos_completos():
    assert resolver_regla("GET", "/api/authentication") is None


def test_resolver_lee_el_mapa_al_momento_de_la_llamada(monkeypatch):
    # Permite sumar servicios nuevos solo agregando líneas al mapa
    monkeypatch.setitem(mapa_rutas.MAPA_MODULOS, "/api/animales", MODULO_FICHAS_EJEMPLARES)

    regla = resolver_regla("GET", "/api/animales/5")

    assert regla.nivel == NIVEL_MODULO
    assert regla.codigo_servicio == MODULO_FICHAS_EJEMPLARES
