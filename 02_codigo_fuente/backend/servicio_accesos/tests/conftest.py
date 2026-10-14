import os

# Datos de configuración momentaneos para que pase el pipeline
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-con-longitud-suficiente")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_HOURS", "8")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
import src.modelos  # noqa: F401  (registra los modelos en Base.metadata)
from src.main import app
from src.logica_negocio.auth import create_access_token, hash_password
from src.modelos.rol_modulo_model import RolModel
from src.modelos.usuario_model import UsuarioModel

ID_ROL_ADMIN = 1
ID_ROL_USUARIO = 2
PASSWORD = "password123"


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    engine.dispose()


@pytest.fixture
def db(session_factory):
    session = session_factory()
    session.add_all([
        RolModel(id_rol=ID_ROL_ADMIN, nombre_rol="Administrador"),
        RolModel(id_rol=ID_ROL_USUARIO, nombre_rol="Usuario"),
    ])
    session.commit()
    yield session
    session.close()


@pytest.fixture
def crear_usuario_db(db):
    """Fábrica de usuarios persistidos con contraseña PASSWORD."""
    def _crear(correo="user@test.com", id_rol=ID_ROL_USUARIO, activo=True, nombre="Ana", apellido="Pérez"):
        usuario = UsuarioModel(
            nombre=nombre, apellido=apellido, correo=correo,
            password_hash=hash_password(PASSWORD), id_rol=id_rol, activo=activo,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario
    return _crear


def _token(id_rol):
    return create_access_token({"sub": "token@test.com", "id_usuario": 99, "id_rol": id_rol})


@pytest.fixture
def headers_admin():
    return {"Authorization": f"Bearer {_token(ID_ROL_ADMIN)}"}


@pytest.fixture
def headers_no_admin():
    return {"Authorization": f"Bearer {_token(ID_ROL_USUARIO)}"}


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()
