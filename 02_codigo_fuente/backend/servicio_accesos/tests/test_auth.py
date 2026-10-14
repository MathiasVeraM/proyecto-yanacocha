from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from src.config import ALGORITHM, SECRET_KEY
from src.logica_negocio.auth import (
    create_access_token, hash_password, verificar_es_admin,
    verificar_token_access, verify_password,
)


def test_hash_y_verificacion():
    hashed = hash_password("secreto123")
    assert hashed != "secreto123"
    assert verify_password("secreto123", hashed)
    assert not verify_password("otra", hashed)


def test_hashes_de_la_misma_password_son_distintos():
    assert hash_password("secreto123") != hash_password("secreto123")


def test_token_contiene_claims_y_expira_en_horas():
    token = create_access_token({"sub": "a@b.com", "id_usuario": 5, "id_rol": 1})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert (payload["sub"], payload["id_usuario"], payload["id_rol"]) == ("a@b.com", 5, 1)
    restante = datetime.fromtimestamp(payload["exp"], timezone.utc) - datetime.now(timezone.utc)
    assert timedelta(hours=7, minutes=59) < restante <= timedelta(hours=8)


def test_create_access_token_no_muta_la_entrada():
    datos = {"sub": "a@b.com"}
    create_access_token(datos)
    assert datos == {"sub": "a@b.com"}


def test_verificar_token_valido_devuelve_payload():
    token = create_access_token({"sub": "a@b.com", "id_rol": 2})
    assert verificar_token_access(token)["sub"] == "a@b.com"


def _codificar(payload, clave=SECRET_KEY):
    return jwt.encode(payload, clave, algorithm=ALGORITHM)


@pytest.mark.parametrize("token", [
    _codificar({"sub": "a@b.com", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}),
    _codificar({"sub": "a@b.com"}, clave="x" * 32),
    "esto-no-es-un-jwt",
    _codificar({"id_rol": 1}),
], ids=["vencido", "firma-incorrecta", "mal-formado", "sin-sub"])
def test_verificar_token_invalido_da_401(token):
    with pytest.raises(HTTPException) as exc:
        verificar_token_access(token)
    assert exc.value.status_code == 401


def test_verificar_es_admin_permite_rol_1():
    payload = {"sub": "a@b.com", "id_rol": 1}
    assert verificar_es_admin(payload) == payload


@pytest.mark.parametrize("payload", [{"id_rol": 2}, {"sub": "a@b.com"}])
def test_verificar_es_admin_rechaza_otros_roles(payload):
    with pytest.raises(HTTPException) as exc:
        verificar_es_admin(payload)
    assert exc.value.status_code == 403
