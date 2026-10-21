from datetime import datetime, timedelta, timezone

import jwt
import pytest

URL = "/api/animales"


def test_sin_token_401(client):
    assert client.get(URL).status_code == 401


def test_token_invalido_401(client):
    assert client.get(URL, headers={"Authorization": "Bearer basura"}).status_code == 401


def test_token_expirado_401(client, headers_con_token):
    vencido = datetime.now(timezone.utc) - timedelta(minutes=1)
    assert client.get(URL, headers=headers_con_token(exp=vencido)).status_code == 401


@pytest.mark.parametrize("campo_faltante", ["sub", "id_usuario", "exp"])
def test_token_incompleto_401(client, headers_con_token, campo_faltante):
    # crear_token quita los campos que valen None
    assert client.get(URL, headers=headers_con_token(**{campo_faltante: None})).status_code == 401


def test_token_firmado_con_otra_clave_401(client):
    falso = jwt.encode(
        {"sub": "x", "id_usuario": 1, "id_rol": 1, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "otra-clave-que-no-es-la-del-servicio-1234",
        algorithm="HS256",
    )
    assert client.get(URL, headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_rol_sin_el_modulo_403(client, headers_sin_permiso):
    assert client.get(URL, headers=headers_sin_permiso).status_code == 403


def test_modulos_como_texto_no_da_permiso_403(client, headers_con_token):
    # Un string coincidiría por subcadena con el código, por eso se exige una lista
    headers = headers_con_token(modulos="servicio-gestion-animal-y-mas")
    assert client.get(URL, headers=headers).status_code == 403


def test_rol_con_el_modulo_200(client, headers_con_permiso):
    assert client.get(URL, headers=headers_con_permiso).status_code == 200


def test_admin_sin_modulo_en_token_200(client, headers_admin):
    assert client.get(URL, headers=headers_admin).status_code == 200


def test_raiz_no_exige_token(client):
    assert client.get("/").json() == {"message": "Servicio de Gestión Animal operativo"}
