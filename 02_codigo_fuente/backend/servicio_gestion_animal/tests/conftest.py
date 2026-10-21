import os

# Datos de configuración momentaneos para que pase el pipeline
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-con-longitud-suficiente")
os.environ.setdefault("ALGORITHM", "HS256")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import DB_SCHEMA
from src.database import Base
import src.modelos  # noqa: F401  (registra los modelos en Base.metadata)
from src.modelos.animal_model import AnimalModel, DiagnosticoModel

ID_USUARIO_VETERINARIO = 7


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
