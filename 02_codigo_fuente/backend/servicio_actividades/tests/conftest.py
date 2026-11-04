"""Asume src.main.app, src.database.get_db y modelos SQLAlchemy en src.modelos."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://localhost/test")
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-con-longitud-suficiente")
os.environ.setdefault("ALGORITHM", "HS256")

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Column, Integer, Table, create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import ALGORITHM, SECRET_KEY
from src.database import Base, get_db

ID_USUARIO_PRUEBA = 301
ID_ANIMAL_PRUEBA = 101
ID_RECINTO_PRUEBA = 201
ID_ROL_ADMIN = 1
ID_ROL_VETERINARIA = 2
ID_ROL_MANEJO_ANIMAL = 3
ID_ROL_VOLUNTARIO = 4
CODIGO_MODULO = "servicio-actividades"

# Tablas mínimas de los servicios externos para que las FK funcionen en SQLite.
Table(
    "animal",
    Base.metadata,
    Column("id_animal", Integer, primary_key=True),
    schema="gestion_animal",
)
Table(
    "recinto",
    Base.metadata,
    Column("id_recinto", Integer, primary_key=True),
    schema="gestion_animal",
)
Table(
    "usuario",
    Base.metadata,
    Column("id_usuario", Integer, primary_key=True),
    schema="public",
)

import src.modelos  # noqa: F401  (registra los modelos en Base.metadata)
from src.main import app


def crear_token(id_rol=ID_ROL_MANEJO_ANIMAL, id_usuario=ID_USUARIO_PRUEBA, modulos=None):
    payload = {
        "sub": "prueba@test.com",
        "id_usuario": id_usuario,
        "id_rol": id_rol,
        "modulos": modulos if modulos is not None else [CODIGO_MODULO],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        execution_options={
            "schema_translate_map": {
                "actividades": None,
                "gestion_animal": None,
                "public": None,
            }
        },
    )

    @event.listens_for(engine, "connect")
    def _activar_fk(conexion, _):
        conexion.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    engine.dispose()


@pytest.fixture
def db(session_factory):
    session = session_factory()
    session.execute(Base.metadata.tables["gestion_animal.animal"].insert().values(id_animal=ID_ANIMAL_PRUEBA))
    session.execute(Base.metadata.tables["gestion_animal.recinto"].insert().values(id_recinto=ID_RECINTO_PRUEBA))
    session.execute(Base.metadata.tables["public.usuario"].insert().values(id_usuario=ID_USUARIO_PRUEBA))
    session.commit()
    yield session
    session.close()


@pytest.fixture
def headers_con_permiso():
    return {"Authorization": f"Bearer {crear_token()}"}


@pytest.fixture
def headers_admin():
    return {"Authorization": f"Bearer {crear_token(id_rol=ID_ROL_ADMIN, modulos=[])}"}


@pytest.fixture
def headers_rol():
    def _crear(id_rol, modulos=None):
        return {"Authorization": f"Bearer {crear_token(id_rol=id_rol, modulos=modulos)}"}

    return _crear


@pytest.fixture
def client(db, headers_con_permiso):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, headers=headers_con_permiso) as cliente:
        yield cliente
    app.dependency_overrides.clear()


@pytest.fixture
def animal_prueba():
    return {"id_animal": ID_ANIMAL_PRUEBA}


@pytest.fixture
def recinto_prueba():
    return {"id_recinto": ID_RECINTO_PRUEBA}


@pytest.fixture
def usuario_prueba():
    return {"id_usuario": ID_USUARIO_PRUEBA}


@pytest.fixture
def dieta_con_alimentos(client, animal_prueba):
    respuesta = client.post(
        "/api/actividades/dietas",
        json={
            "id_animal": animal_prueba["id_animal"],
            "fecha_inicio": "2026-01-01",
            "frecuencia_valor": 1,
            "frecuencia_unidad": "dias",
            "alimentos": [
                {"nombre_alimento": "Fruta", "cantidad_gramos": 150},
                {"nombre_alimento": "Semillas", "cantidad_gramos": 35.5},
            ],
        },
    )
    assert respuesta.status_code == 201
    return respuesta.json()


@pytest.fixture
def crear_actividad(client, animal_prueba, recinto_prueba):
    def _crear(tipo_actividad, **extra):
        datos = {
            "tipo_actividad": tipo_actividad,
            "fecha_programada": "2026-01-02",
            "hora_programada": "09:30:00",
            "duracion_horas": 0,
            "duracion_minutos": 30,
            **extra,
        }
        if tipo_actividad == "limpieza":
            datos["id_recinto"] = recinto_prueba["id_recinto"]
            ruta = "/api/actividades/limpiezas"
        else:
            datos["id_animal"] = animal_prueba["id_animal"]
            rutas = {
                "alimentacion": "/api/actividades/alimentaciones",
                "enriquecimiento": "/api/actividades/enriquecimientos",
                "entrenamiento": "/api/actividades/entrenamientos",
            }
            ruta = rutas[tipo_actividad]
        return client.post(ruta, json=datos)

    return _crear


@pytest.fixture
def actividad_alimentacion(crear_actividad, dieta_con_alimentos):
    respuesta = crear_actividad(
        "alimentacion",
        hora_programada="08:00:00",
        id_dieta=dieta_con_alimentos["id_dieta"],
    )
    assert respuesta.status_code == 201
    return respuesta.json()


@pytest.fixture
def actividad_enriquecimiento(crear_actividad):
    respuesta = crear_actividad(
        "enriquecimiento",
        tipo_enriquecimiento="sensorial",
        descripcion_estimulo="Ramas con hojas frescas",
    )
    assert respuesta.status_code == 201
    return respuesta.json()


@pytest.fixture
def actividad_entrenamiento(crear_actividad):
    respuesta = crear_actividad(
        "entrenamiento",
        objetivo_entrenamiento="Acudir a la estación de manejo",
        tipo_refuerzo="Refuerzo positivo",
        duracion_horas=1,
        duracion_minutos=15,
    )
    assert respuesta.status_code == 201
    return respuesta.json()


@pytest.fixture
def actividad_limpieza(crear_actividad):
    respuesta = crear_actividad(
        "limpieza",
        duracion_horas=1,
        duracion_minutos=0,
    )
    assert respuesta.status_code == 201
    return respuesta.json()
