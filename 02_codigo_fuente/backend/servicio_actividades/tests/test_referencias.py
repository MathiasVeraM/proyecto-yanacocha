"""GET /api/actividades/referencias: ejemplares, recintos y usuarios para Planificación."""

import pytest

from src.config import ID_ROL_MANEJO_ANIMAL, ID_ROL_VETERINARIA, ID_ROL_VOLUNTARIO
from src.database import Base

URL = "/api/actividades/referencias"
ID_ROL_ADMIN = 1


def _tabla(nombre):
    return Base.metadata.tables[nombre]


@pytest.fixture
def datos(db):
    """Un ejemplar con su especie y recinto, otro recinto vacío y dos usuarios (uno inactivo)."""
    recintos = _tabla("gestion_animal.recinto")
    animales = _tabla("gestion_animal.animal")
    usuarios = _tabla("public.usuario")
    db.execute(
        _tabla("gestion_animal.taxonomia").insert().values(
            id_taxonomia=1, nombre_comun="Oso de anteojos", especie="Tremarctos ornatus", clase="Mammalia"
        )
    )
    db.execute(
        recintos.update().where(recintos.c.id_recinto == 201)
        .values(nombre_recinto="Sector de osos", tipo="Exterior", capacidad=4, estado="disponible")
    )
    db.execute(
        recintos.insert().values(
            id_recinto=202, nombre_recinto="Aviario", tipo=None, capacidad=None, estado="en_limpieza"
        )
    )
    db.execute(
        animales.update().where(animales.c.id_animal == 101)
        .values(codigo_animal="YC-2026-0001", nombre="Yaku", id_taxonomia=1, id_recinto=201, estado_actual="en_centro")
    )
    db.execute(usuarios.update().where(usuarios.c.id_usuario == 301).values(nombre="Ana", apellido="Pérez", activo=True))
    db.execute(usuarios.insert().values(id_usuario=302, nombre="Beto", apellido="Álvarez", activo=False))
    db.commit()


def test_devuelve_ejemplares_recintos_y_usuarios(client, datos):
    respuesta = client.get(URL)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["animales"] == [
        {
            "id_animal": 101,
            "codigo_animal": "YC-2026-0001",
            "nombre": "Yaku",
            "id_taxonomia": 1,
            "id_recinto": 201,
            "estado_actual": "en_centro",
            "taxonomia": {
                "id_taxonomia": 1,
                "nombre_comun": "Oso de anteojos",
                "especie": "Tremarctos ornatus",
                "clase": "Mammalia",
            },
            "recinto": {
                "id_recinto": 201,
                "nombre_recinto": "Sector de osos",
                "tipo": "Exterior",
                "capacidad": 4,
                "estado": "disponible",
            },
        }
    ]
    # Ordenados por nombre; incluye el recinto sin ejemplares (se necesita para crear limpiezas)
    assert [r["nombre_recinto"] for r in cuerpo["recintos"]] == ["Aviario", "Sector de osos"]
    assert cuerpo["recintos"][0] == {
        "id_recinto": 202, "nombre_recinto": "Aviario", "tipo": None, "capacidad": None, "estado": "en_limpieza",
    }


def test_incluye_usuarios_inactivos_ordenados_por_apellido(client, datos):
    usuarios = client.get(URL).json()["usuarios"]

    assert usuarios == [
        {"id_usuario": 302, "nombre": "Beto", "apellido": "Álvarez", "activo": False},
        {"id_usuario": 301, "nombre": "Ana", "apellido": "Pérez", "activo": True},
    ]


def test_no_expone_correo_ni_rol_ni_datos_de_la_ficha(client, datos):
    cuerpo = client.get(URL).json()

    assert set(cuerpo["usuarios"][0]) == {"id_usuario", "nombre", "apellido", "activo"}
    assert "url_imagen" not in cuerpo["animales"][0]
    assert "fecha_ingreso" not in cuerpo["animales"][0]


def test_ejemplar_sin_especie_no_aparece_y_el_resto_si(client, db):
    # La fixture base no tiene especie: su ejemplar no aparece; el recinto y el usuario sí
    cuerpo = client.get(URL).json()

    assert cuerpo["animales"] == []
    assert len(cuerpo["recintos"]) == 1
    assert len(cuerpo["usuarios"]) == 1


@pytest.mark.parametrize("id_rol", [ID_ROL_ADMIN, ID_ROL_VETERINARIA, ID_ROL_MANEJO_ANIMAL, ID_ROL_VOLUNTARIO])
def test_cualquier_rol_la_consulta_sin_permisos_de_otros_modulos(client, headers_rol, datos, id_rol):
    # El token solo trae el módulo de planificación: no hace falta Fichas ni Accesos
    respuesta = client.get(URL, headers=headers_rol(id_rol, modulos=["servicio-actividades"]))
    assert respuesta.status_code == 200


def test_exige_token(client, datos):
    assert client.get(URL, headers={"Authorization": ""}).status_code == 401


def test_la_ruta_no_se_confunde_con_una_actividad(client, datos):
    # /referencias no debe interpretarse como GET /api/actividades/{id_actividad}
    assert client.get(URL).status_code != 422
