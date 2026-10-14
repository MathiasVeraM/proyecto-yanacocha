import pytest
from fastapi import HTTPException

from src.esquemas.usuario_schema import UsuarioCreate, UsuarioUpdate
from src.logica_negocio.auth import verify_password
from src.logica_negocio.usuario_service import UsuarioService
from tests.conftest import ID_ROL_USUARIO, PASSWORD


def _nuevo(**cambios):
    datos = dict(nombre="Luis", apellido="Gómez", correo="luis@test.com",
                 password=PASSWORD, id_rol=ID_ROL_USUARIO)
    datos.update(cambios)
    return UsuarioCreate(**datos)


def test_listar_usuarios(db, crear_usuario_db):
    crear_usuario_db("a@test.com")
    crear_usuario_db("b@test.com")
    assert len(UsuarioService.listar_usuarios(db)) == 2


def test_crear_usuario_hashea_password(db):
    usuario = UsuarioService.crear_nuevo_usuario(db, _nuevo())
    assert usuario.password_hash != PASSWORD
    assert verify_password(PASSWORD, usuario.password_hash)
    assert usuario.activo is True


def test_crear_correo_duplicado_400(db, crear_usuario_db):
    crear_usuario_db("luis@test.com")
    with pytest.raises(HTTPException) as exc:
        UsuarioService.crear_nuevo_usuario(db, _nuevo())
    assert exc.value.status_code == 400


def test_crear_rol_inexistente_400(db):
    with pytest.raises(HTTPException) as exc:
        UsuarioService.crear_nuevo_usuario(db, _nuevo(id_rol=999))
    assert exc.value.status_code == 400


def test_actualizar_usuario_inexistente_404(db):
    with pytest.raises(HTTPException) as exc:
        UsuarioService.actualizar_datos_usuario(db, 999, UsuarioUpdate(nombre="X"))
    assert exc.value.status_code == 404


def test_actualizar_correo_de_otro_usuario_400(db, crear_usuario_db):
    crear_usuario_db("a@test.com")
    b = crear_usuario_db("b@test.com")
    with pytest.raises(HTTPException) as exc:
        UsuarioService.actualizar_datos_usuario(db, b.id_usuario, UsuarioUpdate(correo="a@test.com"))
    assert exc.value.status_code == 400


def test_actualizar_al_mismo_correo_permitido(db, crear_usuario_db):
    a = crear_usuario_db("a@test.com")
    resultado = UsuarioService.actualizar_datos_usuario(
        db, a.id_usuario, UsuarioUpdate(correo="a@test.com", nombre="Nuevo"))
    assert resultado.nombre == "Nuevo"


def test_actualizar_a_correo_libre(db, crear_usuario_db):
    a = crear_usuario_db("a@test.com")
    resultado = UsuarioService.actualizar_datos_usuario(db, a.id_usuario, UsuarioUpdate(correo="nuevo@test.com"))
    assert resultado.correo == "nuevo@test.com"


def test_actualizar_rol_inexistente_400(db, crear_usuario_db):
    a = crear_usuario_db()
    with pytest.raises(HTTPException) as exc:
        UsuarioService.actualizar_datos_usuario(db, a.id_usuario, UsuarioUpdate(id_rol=999))
    assert exc.value.status_code == 400


def test_actualizar_ignora_nulls_y_solo_cambia_lo_enviado(db, crear_usuario_db):
    a = crear_usuario_db(nombre="Ana", apellido="Pérez")
    resultado = UsuarioService.actualizar_datos_usuario(
        db, a.id_usuario, UsuarioUpdate(nombre=None, apellido="Nuevo"))
    assert (resultado.nombre, resultado.apellido) == ("Ana", "Nuevo")


def test_actualizar_hashea_password(db, crear_usuario_db):
    a = crear_usuario_db()
    resultado = UsuarioService.actualizar_datos_usuario(db, a.id_usuario, UsuarioUpdate(password="otra-password"))
    assert verify_password("otra-password", resultado.password_hash)


def test_actualizar_rol_valido(db, crear_usuario_db):
    a = crear_usuario_db()
    resultado = UsuarioService.actualizar_datos_usuario(db, a.id_usuario, UsuarioUpdate(id_rol=1))
    assert resultado.id_rol == 1


def test_reactivar_con_activo_true(db, crear_usuario_db):
    a = crear_usuario_db(activo=False)
    resultado = UsuarioService.actualizar_datos_usuario(db, a.id_usuario, UsuarioUpdate(activo=True))
    assert resultado.activo is True


def test_desactivar_usuario(db, crear_usuario_db):
    a = crear_usuario_db()
    assert UsuarioService.desactivar_usuario(db, a.id_usuario).activo is False


def test_desactivar_inexistente_404(db):
    with pytest.raises(HTTPException) as exc:
        UsuarioService.desactivar_usuario(db, 999)
    assert exc.value.status_code == 404
