import pytest
from fastapi import HTTPException

from src.esquemas.rol_modulo_schema import ModuloUpdate, RolUpdate
from src.logica_negocio.rol_modulo_service import RolModuloService
from src.modelos.rol_modulo_model import ModuloModel, RolModel, RolPermisoModel

ID_ADMIN = 1
ID_OTRO = 2


def _pares_permisos(db):
    return sorted((p.id_rol, p.id_modulo) for p in db.query(RolPermisoModel).all())


def _codigo_error(funcion, *args):
    with pytest.raises(HTTPException) as exc:
        funcion(*args)
    return exc.value.status_code


# --- Editar rol ---

def test_actualizar_rol(db):
    rol = RolModuloService.actualizar_rol(db, ID_OTRO, RolUpdate(nombre_rol="Veterinaria", descripcion="Vet"))
    assert (rol.nombre_rol, rol.descripcion) == ("Veterinaria", "Vet")


def test_actualizar_rol_parcial_conserva_otros_campos(db):
    RolModuloService.actualizar_rol(db, ID_OTRO, RolUpdate(descripcion="Nueva"))
    rol = db.get(RolModel, ID_OTRO)
    assert (rol.nombre_rol, rol.descripcion) == ("Usuario", "Nueva")


def test_actualizar_rol_con_su_mismo_nombre_es_valido(db):
    rol = RolModuloService.actualizar_rol(db, ID_OTRO, RolUpdate(nombre_rol="Usuario", descripcion="x"))
    assert rol.descripcion == "x"


def test_actualizar_rol_inexistente_404(db):
    assert _codigo_error(RolModuloService.actualizar_rol, db, 999, RolUpdate(descripcion="x")) == 404


def test_actualizar_rol_nombre_duplicado_400(db):
    assert _codigo_error(RolModuloService.actualizar_rol, db, ID_OTRO, RolUpdate(nombre_rol="Administrador")) == 400


def test_actualizar_rol_admin_permite_cambiar_descripcion(db):
    rol = RolModuloService.actualizar_rol(db, ID_ADMIN, RolUpdate(descripcion="Acceso total"))
    assert rol.descripcion == "Acceso total"


# --- Eliminar rol ---

def test_eliminar_rol(db):
    RolModuloService.eliminar_rol(db, ID_OTRO)
    assert db.get(RolModel, ID_OTRO) is None


def test_eliminar_rol_elimina_sus_permisos(db, crear_modulo_db):
    modulo = crear_modulo_db()
    RolModuloService.asignar_permiso(db, ID_ADMIN, modulo.id_modulo)
    RolModuloService.asignar_permiso(db, ID_OTRO, modulo.id_modulo)
    RolModuloService.eliminar_rol(db, ID_OTRO)
    assert _pares_permisos(db) == [(ID_ADMIN, modulo.id_modulo)]


def test_eliminar_rol_inexistente_404(db):
    assert _codigo_error(RolModuloService.eliminar_rol, db, 999) == 404


def test_eliminar_rol_administrador_409(db):
    assert _codigo_error(RolModuloService.eliminar_rol, db, ID_ADMIN) == 409
    assert db.get(RolModel, ID_ADMIN) is not None


def test_eliminar_rol_con_usuarios_asignados_409(db, crear_usuario_db):
    crear_usuario_db(id_rol=ID_OTRO)
    assert _codigo_error(RolModuloService.eliminar_rol, db, ID_OTRO) == 409
    assert db.get(RolModel, ID_OTRO) is not None


# --- Editar módulo ---

def test_actualizar_modulo(db, crear_modulo_db):
    modulo = crear_modulo_db()
    actualizado = RolModuloService.actualizar_modulo(
        db, modulo.id_modulo, ModuloUpdate(nombre_modulo="Planificación", codigo_servicio="servicio-actividades")
    )
    assert (actualizado.nombre_modulo, actualizado.codigo_servicio) == ("Planificación", "servicio-actividades")


def test_actualizar_modulo_parcial_conserva_otros_campos(db, crear_modulo_db):
    modulo = crear_modulo_db()
    actualizado = RolModuloService.actualizar_modulo(db, modulo.id_modulo, ModuloUpdate(codigo_servicio="nuevo"))
    assert (actualizado.nombre_modulo, actualizado.codigo_servicio) == ("Fichas de ejemplares", "nuevo")


def test_actualizar_modulo_con_su_mismo_nombre_es_valido(db, crear_modulo_db):
    modulo = crear_modulo_db()
    actualizado = RolModuloService.actualizar_modulo(
        db, modulo.id_modulo, ModuloUpdate(nombre_modulo=modulo.nombre_modulo, codigo_servicio="otro")
    )
    assert actualizado.codigo_servicio == "otro"


def test_actualizar_modulo_inexistente_404(db):
    assert _codigo_error(RolModuloService.actualizar_modulo, db, 999, ModuloUpdate(codigo_servicio="x")) == 404


def test_actualizar_modulo_nombre_duplicado_400(db, crear_modulo_db):
    crear_modulo_db("M1", "m1")
    m2 = crear_modulo_db("M2", "m2")
    assert _codigo_error(RolModuloService.actualizar_modulo, db, m2.id_modulo, ModuloUpdate(nombre_modulo="M1")) == 400


# --- Eliminar módulo ---

def test_eliminar_modulo(db, crear_modulo_db):
    modulo = crear_modulo_db()
    RolModuloService.eliminar_modulo(db, modulo.id_modulo)
    assert db.get(ModuloModel, modulo.id_modulo) is None


def test_eliminar_modulo_elimina_sus_permisos_en_cascada(db, crear_modulo_db):
    m1, m2 = crear_modulo_db("M1", "m1"), crear_modulo_db("M2", "m2")
    for id_rol in (ID_ADMIN, ID_OTRO):
        RolModuloService.asignar_permiso(db, id_rol, m1.id_modulo)
    RolModuloService.asignar_permiso(db, ID_OTRO, m2.id_modulo)
    RolModuloService.eliminar_modulo(db, m1.id_modulo)
    assert _pares_permisos(db) == [(ID_OTRO, m2.id_modulo)]


def test_eliminar_modulo_inexistente_404(db):
    assert _codigo_error(RolModuloService.eliminar_modulo, db, 999) == 404


# --- Asignar permiso ---

def test_asignar_permiso(db, crear_modulo_db):
    modulo = crear_modulo_db()
    RolModuloService.asignar_permiso(db, ID_OTRO, modulo.id_modulo)
    assert _pares_permisos(db) == [(ID_OTRO, modulo.id_modulo)]


def test_asignar_permiso_es_idempotente(db, crear_modulo_db):
    modulo = crear_modulo_db()
    RolModuloService.asignar_permiso(db, ID_OTRO, modulo.id_modulo)
    RolModuloService.asignar_permiso(db, ID_OTRO, modulo.id_modulo)
    assert _pares_permisos(db) == [(ID_OTRO, modulo.id_modulo)]


def test_asignar_permiso_rol_inexistente_404(db, crear_modulo_db):
    modulo = crear_modulo_db()
    assert _codigo_error(RolModuloService.asignar_permiso, db, 999, modulo.id_modulo) == 404


def test_asignar_permiso_modulo_inexistente_404(db):
    assert _codigo_error(RolModuloService.asignar_permiso, db, ID_OTRO, 999) == 404
    assert _pares_permisos(db) == []


# --- Quitar permiso ---

def test_quitar_permiso(db, crear_modulo_db):
    modulo = crear_modulo_db()
    RolModuloService.asignar_permiso(db, ID_OTRO, modulo.id_modulo)
    RolModuloService.quitar_permiso(db, ID_OTRO, modulo.id_modulo)
    assert _pares_permisos(db) == []


def test_quitar_permiso_inexistente_es_idempotente(db, crear_modulo_db):
    modulo = crear_modulo_db()
    RolModuloService.quitar_permiso(db, ID_OTRO, modulo.id_modulo)
    assert _pares_permisos(db) == []


def test_quitar_permiso_rol_inexistente_404(db, crear_modulo_db):
    modulo = crear_modulo_db()
    assert _codigo_error(RolModuloService.quitar_permiso, db, 999, modulo.id_modulo) == 404


def test_quitar_permiso_modulo_inexistente_404(db):
    assert _codigo_error(RolModuloService.quitar_permiso, db, ID_OTRO, 999) == 404


def test_quitar_permiso_al_administrador_409(db, crear_modulo_db):
    modulo = crear_modulo_db()
    RolModuloService.asignar_permiso(db, ID_ADMIN, modulo.id_modulo)
    assert _codigo_error(RolModuloService.quitar_permiso, db, ID_ADMIN, modulo.id_modulo) == 409
    assert _pares_permisos(db) == [(ID_ADMIN, modulo.id_modulo)]


# --- Matriz roles x módulos ---

def test_matriz_vacia_con_roles_sin_modulos(db):
    matriz = RolModuloService.obtener_matriz(db)
    assert [r["id_rol"] for r in matriz["roles"]] == [ID_ADMIN, ID_OTRO]
    assert matriz["modulos"] == []
    assert matriz["permisos"] == []


def test_matriz_incluye_roles_modulos_y_permisos(db, crear_modulo_db):
    m1, m2 = crear_modulo_db("M1", "m1"), crear_modulo_db("M2", "m2")
    RolModuloService.asignar_permiso(db, ID_ADMIN, m1.id_modulo)
    RolModuloService.asignar_permiso(db, ID_ADMIN, m2.id_modulo)
    RolModuloService.asignar_permiso(db, ID_OTRO, m2.id_modulo)

    matriz = RolModuloService.obtener_matriz(db)

    assert {m["id_modulo"]: m["nombre_modulo"] for m in matriz["modulos"]} == {
        m1.id_modulo: "M1", m2.id_modulo: "M2",
    }
    assert sorted((p["id_rol"], p["id_modulo"]) for p in matriz["permisos"]) == [
        (ID_ADMIN, m1.id_modulo), (ID_ADMIN, m2.id_modulo), (ID_OTRO, m2.id_modulo),
    ]


def test_matriz_incluye_total_de_usuarios_por_rol(db, crear_usuario_db):
    crear_usuario_db(correo="a@test.com", id_rol=ID_OTRO)
    crear_usuario_db(correo="b@test.com", id_rol=ID_OTRO)
    crear_usuario_db(correo="c@test.com", id_rol=ID_ADMIN)
    totales = {r["id_rol"]: r["total_usuarios"] for r in RolModuloService.obtener_matriz(db)["roles"]}
    assert totales == {ID_ADMIN: 1, ID_OTRO: 2}


def test_matriz_incluye_datos_del_rol(db):
    rol = next(r for r in RolModuloService.obtener_matriz(db)["roles"] if r["id_rol"] == ID_ADMIN)
    assert rol["nombre_rol"] == "Administrador"
    assert "descripcion" in rol
