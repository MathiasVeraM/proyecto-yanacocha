"""Pruebas unitarias de la validación del token y de la revisión de permisos."""
from datetime import timedelta

import pytest
from fastapi import HTTPException

from src.modulos import MODULO_ACCESOS, MODULO_FICHAS_EJEMPLARES
from src.seguridad import ID_ROL_ADMIN, decodificar_token, tiene_acceso


# ---- decodificar_token ----

def test_decodifica_un_token_valido(crear_token):
    token = crear_token(id_rol=2, modulos=[MODULO_ACCESOS], sub="ana@test.com")

    payload = decodificar_token(token)

    assert payload["sub"] == "ana@test.com"
    assert payload["id_rol"] == 2
    assert payload["modulos"] == [MODULO_ACCESOS]


def _error_de(token):
    with pytest.raises(HTTPException) as exc:
        decodificar_token(token)
    return exc.value


@pytest.mark.parametrize(
    "construir",
    [
        lambda crear: crear(clave="otra-clave-distinta-de-la-del-gateway-123"),
        lambda crear: crear(expira_en=timedelta(seconds=-5)),
        lambda crear: crear(sub=None),
        lambda crear: crear(clave="clave-solo-para-pruebas-con-longitud-suficiente", algoritmo="HS512"),
        lambda crear: "esto-no-es-un-jwt",
        lambda crear: "",
    ],
    ids=["otra-clave", "expirado", "sin-sub", "otro-algoritmo", "basura", "vacio"],
)
def test_token_invalido_lanza_401(crear_token, construir):
    error = _error_de(construir(crear_token))

    assert error.status_code == 401
    assert error.headers == {"WWW-Authenticate": "Bearer"}


# ---- tiene_acceso ----

def test_el_administrador_tiene_acceso_a_cualquier_modulo():
    payload = {"id_rol": ID_ROL_ADMIN}

    assert tiene_acceso(payload, MODULO_ACCESOS) is True
    assert tiene_acceso(payload, MODULO_FICHAS_EJEMPLARES) is True


def test_el_administrador_es_el_rol_1():
    assert ID_ROL_ADMIN == 1


def test_acceso_cuando_el_modulo_esta_en_el_token():
    payload = {"id_rol": 2, "modulos": [MODULO_FICHAS_EJEMPLARES, MODULO_ACCESOS]}

    assert tiene_acceso(payload, MODULO_ACCESOS) is True


def test_sin_acceso_cuando_el_modulo_no_esta_en_el_token():
    payload = {"id_rol": 2, "modulos": [MODULO_FICHAS_EJEMPLARES]}

    assert tiene_acceso(payload, MODULO_ACCESOS) is False


@pytest.mark.parametrize("modulos", [[], None, "servicio-accesos", {"servicio-accesos": True}, 5])
def test_sin_acceso_si_modulos_esta_vacio_o_mal_formado(modulos):
    # Un string no debe coincidir por subcadena con el código del módulo
    assert tiene_acceso({"id_rol": 2, "modulos": modulos}, MODULO_ACCESOS) is False


def test_sin_acceso_si_el_token_no_trae_modulos():
    # Tokens emitidos antes de este cambio no traen la lista
    assert tiene_acceso({"id_rol": 2}, MODULO_ACCESOS) is False
