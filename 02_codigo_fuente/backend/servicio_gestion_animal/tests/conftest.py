import os

# Datos de configuración momentaneos para que pase el pipeline
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-con-longitud-suficiente")
os.environ.setdefault("ALGORITHM", "HS256")

from datetime import datetime, timedelta, timezone

import httpx2
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
from src.logica_negocio import inaturalist
from src.modelos.animal_model import AnimalModel, DiagnosticoModel, RecintoModel, TaxonomiaModel

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


def _guardar(db, registro):
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


@pytest.fixture
def crear_taxonomia_db(db):
    """Fábrica de especies del catálogo."""
    def _crear(nombre_comun="Oso de anteojos", especie="Tremarctos ornatus", **extra):
        datos = {"genero": "Tremarctos", "familia": "Ursidae", **extra}
        return _guardar(db, TaxonomiaModel(nombre_comun=nombre_comun, especie=especie, **datos))
    return _crear


@pytest.fixture
def crear_recinto_db(db):
    """Fábrica de recintos."""
    def _crear(nombre_recinto="Sector de osos", **extra):
        return _guardar(db, RecintoModel(nombre_recinto=nombre_recinto, **extra))
    return _crear


@pytest.fixture
def crear_animal_db(db, crear_taxonomia_db, crear_recinto_db):
    """Fábrica de animales; si no se indica especie o recinto, crea unos nuevos."""
    contador = iter(range(1, 1000))

    def _crear(codigo_animal=None, id_taxonomia=None, id_recinto=None, **extra):
        n = next(contador)
        if id_taxonomia is None:
            id_taxonomia = crear_taxonomia_db(nombre_comun=f"Especie {n}", especie=f"Especie prueba{n}").id_taxonomia
        if id_recinto is None:
            id_recinto = crear_recinto_db(nombre_recinto=f"Recinto {n}").id_recinto
        animal = AnimalModel(
            codigo_animal=codigo_animal or f"EP-{n:03d}", id_taxonomia=id_taxonomia, id_recinto=id_recinto, **extra
        )
        return _guardar(db, animal)
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


class INaturalistSimulado:
    """Reemplaza a la API real de iNaturalist: las pruebas nunca salen a internet."""

    def __init__(self):
        self.peticiones: list[httpx2.Request] = []
        self.respuestas: dict[str, httpx2.Response] = {}
        self.error: Exception | None = None

    def responder(self, ruta: str, cuerpo: dict, codigo: int = 200):
        self.respuestas[ruta] = httpx2.Response(codigo, json=cuerpo)

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.peticiones.append(request)
        if self.error:
            raise self.error
        ruta = request.url.path.removeprefix("/v1")
        return self.respuestas.get(ruta, httpx2.Response(200, json={"results": []}))


@pytest.fixture(autouse=True)
def inaturalist_simulado(monkeypatch):
    simulado = INaturalistSimulado()
    monkeypatch.setattr(
        inaturalist,
        "crear_cliente",
        lambda: httpx2.Client(base_url="https://api.inaturalist.org/v1", transport=httpx2.MockTransport(simulado)),
    )
    return simulado
