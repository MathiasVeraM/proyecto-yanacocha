import pytest
from sqlalchemy.exc import IntegrityError

from src.repositorios.rol_modulo_repo import RolModuloRepository
from src.repositorios.usuario_repo import UsuarioRepository


def _datos_usuario(correo="r@test.com"):
    return dict(nombre="R", apellido="T", correo=correo, password_hash="h", id_rol=1)


def test_usuario_crear_y_consultar(db):
    u = UsuarioRepository.crear_usuario(db, _datos_usuario())
    assert u.id_usuario is not None and u.activo is True
    assert UsuarioRepository.obtener_por_correo(db, "r@test.com").id_usuario == u.id_usuario
    assert UsuarioRepository.obtener_por_id(db, u.id_usuario).correo == "r@test.com"
    assert len(UsuarioRepository.obtener_todos(db)) == 1


def test_usuario_inexistente_devuelve_none(db):
    assert UsuarioRepository.obtener_por_correo(db, "no@test.com") is None
    assert UsuarioRepository.obtener_por_id(db, 999) is None


def test_usuario_actualizar(db):
    u = UsuarioRepository.crear_usuario(db, _datos_usuario())
    u = UsuarioRepository.actualizar_usuario(db, u, {"nombre": "Nuevo", "activo": False})
    assert (u.nombre, u.activo) == ("Nuevo", False)


def test_usuario_correo_duplicado_lanza_error(db):
    UsuarioRepository.crear_usuario(db, _datos_usuario())
    with pytest.raises(IntegrityError):
        UsuarioRepository.crear_usuario(db, _datos_usuario())


def test_rol_crear_y_consultar(db):
    rol = RolModuloRepository.crear_rol(db, {"nombre_rol": "Vet", "descripcion": None})
    assert RolModuloRepository.obtener_rol_por_id(db, rol.id_rol).nombre_rol == "Vet"
    assert RolModuloRepository.obtener_rol_por_nombre(db, "Vet").id_rol == rol.id_rol
    assert len(RolModuloRepository.obtener_roles(db)) == 3


def test_rol_inexistente_devuelve_none(db):
    assert RolModuloRepository.obtener_rol_por_id(db, 999) is None
    assert RolModuloRepository.obtener_rol_por_nombre(db, "nada") is None


def test_rol_duplicado_lanza_error(db):
    with pytest.raises(IntegrityError):
        RolModuloRepository.crear_rol(db, {"nombre_rol": "Administrador"})


def test_modulo_crear_y_consultar(db):
    datos = {"nombre_modulo": "Animales", "codigo_servicio": "animales"}
    RolModuloRepository.crear_modulo(db, datos)
    assert RolModuloRepository.obtener_modulo_por_nombre(db, "Animales").codigo_servicio == "animales"
    assert RolModuloRepository.obtener_modulo_por_nombre(db, "nada") is None
    assert len(RolModuloRepository.obtener_modulos(db)) == 1


def test_modulo_duplicado_lanza_error(db):
    datos = {"nombre_modulo": "Animales", "codigo_servicio": "animales"}
    RolModuloRepository.crear_modulo(db, datos)
    with pytest.raises(IntegrityError):
        RolModuloRepository.crear_modulo(db, datos)
