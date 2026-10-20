import jwt
import pytest
from fastapi import HTTPException

from src.config import ALGORITHM, SECRET_KEY
from src.logica_negocio.auth_service import AuthService
from src.logica_negocio.rol_modulo_service import RolModuloService
from tests.conftest import ID_ROL_ADMIN, ID_ROL_USUARIO, PASSWORD


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


def _modulos_del_token(db):
    token = AuthService.iniciar_sesion(db, "user@test.com", PASSWORD)
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["modulos"]


def test_token_incluye_los_modulos_permitidos_del_rol(db, crear_usuario_db, crear_modulo_db):
    crear_usuario_db()
    m1 = crear_modulo_db("Fichas", "servicio-gestion-animal")
    m2 = crear_modulo_db("Planificación", "servicio-actividades")
    RolModuloService.asignar_permiso(db, ID_ROL_USUARIO, m1.id_modulo)
    RolModuloService.asignar_permiso(db, ID_ROL_USUARIO, m2.id_modulo)
    assert sorted(_modulos_del_token(db)) == ["servicio-actividades", "servicio-gestion-animal"]


def test_token_sin_permisos_trae_lista_vacia(db, crear_usuario_db, crear_modulo_db):
    crear_usuario_db()
    crear_modulo_db()
    assert _modulos_del_token(db) == []


def test_token_no_incluye_modulos_de_otros_roles(db, crear_usuario_db, crear_modulo_db):
    crear_usuario_db()
    modulo = crear_modulo_db()
    RolModuloService.asignar_permiso(db, ID_ROL_ADMIN, modulo.id_modulo)
    assert _modulos_del_token(db) == []


def test_token_no_repite_codigos_de_servicio(db, crear_usuario_db, crear_modulo_db):
    crear_usuario_db()
    m1 = crear_modulo_db("Animales", "servicio-gestion-animal")
    m2 = crear_modulo_db("Veterinaria", "servicio-gestion-animal")
    RolModuloService.asignar_permiso(db, ID_ROL_USUARIO, m1.id_modulo)
    RolModuloService.asignar_permiso(db, ID_ROL_USUARIO, m2.id_modulo)
    assert _modulos_del_token(db) == ["servicio-gestion-animal"]


def test_token_refleja_los_permisos_vigentes_al_iniciar_sesion(db, crear_usuario_db, crear_modulo_db):
    crear_usuario_db()
    modulo = crear_modulo_db()
    RolModuloService.asignar_permiso(db, ID_ROL_USUARIO, modulo.id_modulo)
    assert _modulos_del_token(db) == [modulo.codigo_servicio]
    RolModuloService.quitar_permiso(db, ID_ROL_USUARIO, modulo.id_modulo)
    assert _modulos_del_token(db) == []
