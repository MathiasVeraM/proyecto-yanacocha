import pytest
from fastapi import HTTPException

from src.esquemas.rol_modulo_schema import ModuloCreate, RolCreate
from src.logica_negocio.rol_modulo_service import RolModuloService


def test_listar_roles(db):
    assert len(RolModuloService.listar_roles(db)) == 2


def test_crear_rol(db):
    rol = RolModuloService.crear_rol(db, RolCreate(nombre_rol="Veterinario", descripcion="Vet"))
    assert rol.id_rol is not None and rol.descripcion == "Vet"


def test_crear_rol_duplicado_400(db):
    with pytest.raises(HTTPException) as exc:
        RolModuloService.crear_rol(db, RolCreate(nombre_rol="Administrador"))
    assert exc.value.status_code == 400


def test_crear_y_listar_modulos(db):
    assert RolModuloService.listar_modulos(db) == []
    modulo = RolModuloService.crear_modulo(db, ModuloCreate(nombre_modulo="Animales", codigo_servicio="animales"))
    assert modulo.codigo_servicio == "animales"
    assert len(RolModuloService.listar_modulos(db)) == 1


def test_crear_modulo_duplicado_400(db):
    datos = ModuloCreate(nombre_modulo="Animales", codigo_servicio="animales")
    RolModuloService.crear_modulo(db, datos)
    with pytest.raises(HTTPException) as exc:
        RolModuloService.crear_modulo(db, datos)
    assert exc.value.status_code == 400
