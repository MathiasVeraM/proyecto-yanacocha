from src.modelos.rol_modulo_model import RolPermisoModel
from src.repositorios.rol_modulo_repo import RolModuloRepository


# --- Roles: actualizar / eliminar / contar usuarios ---

def test_rol_actualizar(db):
    rol = RolModuloRepository.obtener_rol_por_id(db, 2)
    rol = RolModuloRepository.actualizar_rol(db, rol, {"nombre_rol": "Voluntarios", "descripcion": "Apoyo"})
    assert (rol.nombre_rol, rol.descripcion) == ("Voluntarios", "Apoyo")


def test_rol_eliminar(db):
    rol = RolModuloRepository.obtener_rol_por_id(db, 2)
    RolModuloRepository.eliminar_rol(db, rol)
    assert RolModuloRepository.obtener_rol_por_id(db, 2) is None


def test_contar_usuarios_por_rol(db, crear_usuario_db):
    assert RolModuloRepository.contar_usuarios_por_rol(db, 2) == 0
    crear_usuario_db(correo="a@test.com", id_rol=2)
    crear_usuario_db(correo="b@test.com", id_rol=2)
    crear_usuario_db(correo="c@test.com", id_rol=1)
    assert RolModuloRepository.contar_usuarios_por_rol(db, 2) == 2
    assert RolModuloRepository.contar_usuarios_por_rol(db, 1) == 1


# --- Módulos: consultar por id / actualizar / eliminar ---

def test_modulo_obtener_por_id(db, crear_modulo_db):
    modulo = crear_modulo_db()
    assert RolModuloRepository.obtener_modulo_por_id(db, modulo.id_modulo).nombre_modulo == modulo.nombre_modulo
    assert RolModuloRepository.obtener_modulo_por_id(db, 999) is None


def test_modulo_actualizar(db, crear_modulo_db):
    modulo = crear_modulo_db()
    modulo = RolModuloRepository.actualizar_modulo(
        db, modulo, {"nombre_modulo": "Planificación", "codigo_servicio": "servicio-actividades"}
    )
    assert (modulo.nombre_modulo, modulo.codigo_servicio) == ("Planificación", "servicio-actividades")


def test_modulo_eliminar(db, crear_modulo_db):
    modulo = crear_modulo_db()
    RolModuloRepository.eliminar_modulo(db, modulo)
    assert RolModuloRepository.obtener_modulos(db) == []


# --- Permisos (tabla rol_permiso) ---

def test_asignar_y_consultar_permiso(db, crear_modulo_db):
    modulo = crear_modulo_db()
    assert RolModuloRepository.existe_permiso(db, 2, modulo.id_modulo) is False
    RolModuloRepository.asignar_permiso(db, 2, modulo.id_modulo)
    assert RolModuloRepository.existe_permiso(db, 2, modulo.id_modulo) is True
    permisos = RolModuloRepository.obtener_permisos(db)
    assert [(p.id_rol, p.id_modulo) for p in permisos] == [(2, modulo.id_modulo)]


def test_quitar_permiso(db, crear_modulo_db):
    modulo = crear_modulo_db()
    RolModuloRepository.asignar_permiso(db, 2, modulo.id_modulo)
    RolModuloRepository.quitar_permiso(db, 2, modulo.id_modulo)
    assert RolModuloRepository.existe_permiso(db, 2, modulo.id_modulo) is False
    assert RolModuloRepository.obtener_permisos(db) == []


def test_eliminar_permisos_de_un_rol(db, crear_modulo_db):
    m1, m2 = crear_modulo_db("M1", "m1"), crear_modulo_db("M2", "m2")
    for id_rol in (1, 2):
        RolModuloRepository.asignar_permiso(db, id_rol, m1.id_modulo)
    RolModuloRepository.asignar_permiso(db, 2, m2.id_modulo)
    RolModuloRepository.eliminar_permisos_de_rol(db, 2)
    assert [(p.id_rol, p.id_modulo) for p in db.query(RolPermisoModel).all()] == [(1, m1.id_modulo)]


def test_eliminar_permisos_de_un_modulo(db, crear_modulo_db):
    m1, m2 = crear_modulo_db("M1", "m1"), crear_modulo_db("M2", "m2")
    RolModuloRepository.asignar_permiso(db, 1, m1.id_modulo)
    RolModuloRepository.asignar_permiso(db, 2, m1.id_modulo)
    RolModuloRepository.asignar_permiso(db, 2, m2.id_modulo)
    RolModuloRepository.eliminar_permisos_de_modulo(db, m1.id_modulo)
    assert [(p.id_rol, p.id_modulo) for p in db.query(RolPermisoModel).all()] == [(2, m2.id_modulo)]


# --- Códigos de servicio permitidos para un rol (van dentro del token) ---

def test_codigos_de_servicio_del_rol(db, crear_modulo_db):
    m1, m2 = crear_modulo_db("M1", "servicio-a"), crear_modulo_db("M2", "servicio-b")
    RolModuloRepository.asignar_permiso(db, 2, m1.id_modulo)
    RolModuloRepository.asignar_permiso(db, 2, m2.id_modulo)
    RolModuloRepository.asignar_permiso(db, 1, m1.id_modulo)
    assert sorted(RolModuloRepository.obtener_codigos_servicio_por_rol(db, 2)) == ["servicio-a", "servicio-b"]
    assert RolModuloRepository.obtener_codigos_servicio_por_rol(db, 1) == ["servicio-a"]


def test_codigos_de_servicio_sin_permisos_es_lista_vacia(db, crear_modulo_db):
    crear_modulo_db()
    assert RolModuloRepository.obtener_codigos_servicio_por_rol(db, 2) == []
    assert RolModuloRepository.obtener_codigos_servicio_por_rol(db, 999) == []


def test_codigos_de_servicio_sin_repetir(db, crear_modulo_db):
    # Varios módulos pueden compartir el mismo servicio (p. ej. Animales y Veterinaria)
    m1 = crear_modulo_db("Animales", "servicio-gestion-animal")
    m2 = crear_modulo_db("Veterinaria", "servicio-gestion-animal")
    RolModuloRepository.asignar_permiso(db, 2, m1.id_modulo)
    RolModuloRepository.asignar_permiso(db, 2, m2.id_modulo)
    assert RolModuloRepository.obtener_codigos_servicio_por_rol(db, 2) == ["servicio-gestion-animal"]
