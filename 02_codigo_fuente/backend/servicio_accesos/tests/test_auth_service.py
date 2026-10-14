import jwt
import pytest
from fastapi import HTTPException

from src.config import ALGORITHM, SECRET_KEY
from src.logica_negocio.auth_service import AuthService
from tests.conftest import PASSWORD


def _login(db, correo, password):
    with pytest.raises(HTTPException) as exc:
        AuthService.iniciar_sesion(db, correo, password)
    return exc.value


def test_correo_inexistente_401(db):
    assert _login(db, "nadie@test.com", PASSWORD).status_code == 401


def test_password_incorrecta_401(db, crear_usuario_db):
    crear_usuario_db()
    assert _login(db, "user@test.com", "mala-password").status_code == 401


def test_desactivado_con_password_correcta_403(db, crear_usuario_db):
    crear_usuario_db(activo=False)
    assert _login(db, "user@test.com", PASSWORD).status_code == 403


def test_desactivado_con_password_incorrecta_401(db, crear_usuario_db):
    crear_usuario_db(activo=False)
    assert _login(db, "user@test.com", "mala-password").status_code == 401


def test_activo_none_403(db, crear_usuario_db):
    usuario = crear_usuario_db()
    usuario.activo = None
    assert _login(db, "user@test.com", PASSWORD).status_code == 403


def test_login_correcto_devuelve_token_con_claims(db, crear_usuario_db):
    usuario = crear_usuario_db()
    token = AuthService.iniciar_sesion(db, "user@test.com", PASSWORD)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "user@test.com"
    assert payload["id_usuario"] == usuario.id_usuario
    assert payload["id_rol"] == usuario.id_rol
