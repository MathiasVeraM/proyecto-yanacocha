import os

# Datos de configuración momentaneos para que pase el pipeline
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-con-longitud-suficiente")
os.environ.setdefault("ALGORITHM", "HS256")

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import ALGORITHM, CODIGO_MODULO, DB_SCHEMA, ID_ROL_ADMIN, SECRET_KEY
from src.database import Base, get_db
import src.modelos  # noqa: F401  (registra los modelos en Base.metadata)
from src.main import app
from src.modelos.animal_model import AnimalModel, DiagnosticoModel

ID_USUARIO_VETERINARIO = 7
ID_ROL_VETERINARIA = 2


def crear_token(**datos):
    """Token como los que emite el servicio de accesos; `datos` reemplaza o agrega campos."""
    payload = {
        "sub": "vet@test.com",
        "id_usuario": ID_USUARIO_VETERINARIO,
        "id_rol": ID_ROL_VETERINARIA,
        "modulos": [CODIGO_MODULO],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    payload.update(datos)
    payload = {k: v for k, v in payload.items() if v is not None}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        # SQLite no tiene esquemas: las tablas de gestion_animal se crean sin prefijo
        execution_options={"schema_translate_map": {DB_SCHEMA: None}},
    )

    # SQLite no revisa las llaves foráneas si no se le pide
    @event.listens_for(engine, "connect")
    def _activar_fk(conexion, _):
        conexion.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    engine.dispose()


@pytest.fixture
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def crear_animal_db(db):
    """Fábrica de animales persistidos."""
    def _crear(codigo_animal="YNC-001", nombre_comun="Oso de anteojos", **extra):
        animal = AnimalModel(codigo_animal=codigo_animal, nombre_comun=nombre_comun, **extra)
        db.add(animal)
        db.commit()
        db.refresh(animal)
        return animal
    return _crear


@pytest.fixture
def crear_diagnostico_db(db):
    """Fábrica de diagnósticos persistidos."""
    def _crear(id_animal, diagnostico="Deshidratación leve", **extra):
        registro = DiagnosticoModel(
            id_animal=id_animal, id_usuario=ID_USUARIO_VETERINARIO, diagnostico=diagnostico, **extra
        )
        db.add(registro)
        db.commit()
        db.refresh(registro)
        return registro
    return _crear


@pytest.fixture
def id_veterinario():
    return ID_USUARIO_VETERINARIO


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def headers_con_permiso():
    return {"Authorization": f"Bearer {crear_token()}"}


@pytest.fixture
def headers_admin():
    # El admin entra aunque su token no liste el módulo
    return {"Authorization": f"Bearer {crear_token(id_usuario=1, id_rol=ID_ROL_ADMIN, modulos=[])}"}


@pytest.fixture
def headers_sin_permiso():
    return {"Authorization": f"Bearer {crear_token(id_rol=4, modulos=['servicio-actividades'])}"}


@pytest.fixture
def headers_con_token():
    """Fábrica de cabeceras con un token personalizado, para probar tokens incompletos."""
    def _crear(**datos):
        return {"Authorization": f"Bearer {crear_token(**datos)}"}
    return _crear
