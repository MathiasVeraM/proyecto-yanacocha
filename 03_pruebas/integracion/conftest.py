"""Fixtures de las pruebas de integración.

Todo ocurre por HTTP contra el gateway del docker-compose.test.yml (base de datos efímera).
Variables de entorno que se leen (las exporta el pipeline; en local, ver README.md):
  GATEWAY_URL      opcional, por defecto http://127.0.0.1:8000
  ADMIN_CORREO     correo del administrador de pruebas (el que creó admin-init)
  ADMIN_PASSWORD   su contraseña
  SECRET_KEY       opcional; solo para fabricar tokens vencidos en las pruebas de autenticación
"""
import os
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
import pytest

from ayudas import (
    DOMINIO_CORREOS,
    ROL_MANEJO,
    ROL_VETERINARIA,
    ROL_VOLUNTARIO,
    crear_cliente,
    docker_disponible,
    en_dias,
    exigir,
    id_contenedor,
    iso,
    unico,
    url_gateway,
)

HOSTS_PERMITIDOS = {"localhost", "127.0.0.1", "::1"}


# ---------- Guardia: estas pruebas nunca deben apuntar a un entorno real ----------

def _verificar_entorno_de_pruebas() -> None:
    if os.environ.get("DATABASE_URL"):
        raise pytest.UsageError(
            "DATABASE_URL está definida en el entorno. Las pruebas de integración solo usan HTTP contra "
            "el gateway del compose de pruebas y nunca necesitan una base de datos: quítala para continuar."
        )
    host = urlparse(url_gateway()).hostname
    if host not in HOSTS_PERMITIDOS:
        raise pytest.UsageError(
            f"GATEWAY_URL apunta a '{host}'. Solo se permite localhost/127.0.0.1 (el gateway de "
            "docker-compose.test.yml); estas pruebas crean y modifican datos."
        )
    correo = os.environ.get("ADMIN_CORREO", "")
    if not correo or not os.environ.get("ADMIN_PASSWORD"):
        raise pytest.UsageError("Define ADMIN_CORREO y ADMIN_PASSWORD (el administrador creado por admin-init).")


def pytest_configure(config):
    _verificar_entorno_de_pruebas()


# ---------- Sesión: gateway, administrador y usuarios por rol ----------

@pytest.fixture(scope="session", autouse=True)
def gateway_disponible():
    """Espera a que el gateway responda (compose up --wait ya lo garantiza; esto cubre las carreras)."""
    limite = time.monotonic() + 60
    ultimo_error = None
    with crear_cliente() as cliente:
        while time.monotonic() < limite:
            try:
                if cliente.get("/health").status_code == 200:
                    return
            except httpx.HTTPError as error:
                ultimo_error = error
            time.sleep(1)
    pytest.exit(f"El gateway {url_gateway()} no responde: {ultimo_error}", returncode=2)


@pytest.fixture(scope="session", autouse=True)
def administrador_de_pruebas(gateway_disponible):
    """Falla una sola vez, con un mensaje claro, si el administrador del entorno no coincide con el .env.test."""
    with crear_cliente() as cliente:
        respuesta = cliente.post(
            "/api/auth/login",
            json={"correo": os.environ["ADMIN_CORREO"], "password": os.environ["ADMIN_PASSWORD"]},
        )
    if respuesta.status_code != 200:
        pytest.exit(
            f"No se pudo iniciar sesión con ADMIN_CORREO/ADMIN_PASSWORD (HTTP {respuesta.status_code}). "
            "El entorno de pruebas se levantó con otros valores: recréalo con el mismo .env.test "
            "(docker compose --env-file .env.test -f docker-compose.test.yml down -v, luego up -d --build --wait) "
            "y vuelve a cargar las variables en esta terminal.",
            returncode=2,
        )


def _iniciar_sesion(correo: str, password: str) -> str:
    with crear_cliente() as cliente:
        datos = exigir(cliente.post("/api/auth/login", json={"correo": correo, "password": password}))
    return datos["access_token"]


@pytest.fixture(scope="session")
def api_anonimo():
    with crear_cliente() as cliente:
        yield cliente


@pytest.fixture(scope="session")
def api_admin():
    token = _iniciar_sesion(os.environ["ADMIN_CORREO"], os.environ["ADMIN_PASSWORD"])
    with crear_cliente(token) as cliente:
        yield cliente


@dataclass
class UsuarioPrueba:
    id_usuario: int
    correo: str
    password: str
    id_rol: int
    token: str


def crear_usuario_de_prueba(api_admin, id_rol: int, etiqueta: str) -> UsuarioPrueba:
    """Crea un usuario por la API (solo el administrador puede) y obtiene su token."""
    correo = f"it.{etiqueta}.{secrets.token_hex(4)}@{DOMINIO_CORREOS}"
    password = secrets.token_hex(12)
    creado = exigir(
        api_admin.post(
            "/api/auth/usuarios",
            json={
                "nombre": "Prueba",
                "apellido": etiqueta.capitalize(),
                "correo": correo,
                "password": password,
                "id_rol": id_rol,
            },
        ),
        201,
    )
    return UsuarioPrueba(creado["id_usuario"], correo, password, id_rol, _iniciar_sesion(correo, password))


@pytest.fixture(scope="session")
def usuarios(api_admin):
    """Un usuario por rol. Al terminar se desactivan (la API no permite borrar usuarios)."""
    por_rol = {
        "veterinaria": crear_usuario_de_prueba(api_admin, ROL_VETERINARIA, "veterinaria"),
        "manejo": crear_usuario_de_prueba(api_admin, ROL_MANEJO, "manejo"),
        "voluntario": crear_usuario_de_prueba(api_admin, ROL_VOLUNTARIO, "voluntario"),
    }
    yield por_rol
    for usuario in por_rol.values():
        api_admin.patch(f"/api/auth/usuarios/{usuario.id_usuario}/desactivar")


@pytest.fixture
def usuario_temporal(api_admin):
    """Fábrica de usuarios descartables (se desactivan al terminar la prueba)."""
    creados = []

    def _crear(id_rol: int = ROL_VOLUNTARIO, etiqueta: str = "temporal") -> UsuarioPrueba:
        usuario = crear_usuario_de_prueba(api_admin, id_rol, etiqueta)
        creados.append(usuario)
        return usuario

    yield _crear
    for usuario in creados:
        api_admin.patch(f"/api/auth/usuarios/{usuario.id_usuario}/desactivar")


def _cliente_de(usuario: UsuarioPrueba):
    with crear_cliente(usuario.token) as cliente:
        yield cliente


@pytest.fixture(scope="session")
def api_veterinaria(usuarios):
    yield from _cliente_de(usuarios["veterinaria"])


@pytest.fixture(scope="session")
def api_manejo(usuarios):
    yield from _cliente_de(usuarios["manejo"])


@pytest.fixture(scope="session")
def api_voluntario(usuarios):
    yield from _cliente_de(usuarios["voluntario"])


# ---------- Datos de gestión animal ----------

@pytest.fixture(scope="session")
def taxonomia(api_manejo):
    return exigir(
        api_manejo.post(
            "/api/animales/taxonomia",
            json={
                "nombre_comun": unico("Oso de prueba"),
                "especie": unico("Tremarctos testus"),
                "genero": "Tremarctos",
                "familia": "Ursidae",
                "orden": "Carnivora",
                "clase": "Mammalia",
            },
        ),
        201,
    )


@pytest.fixture
def recinto(api_manejo):
    return exigir(
        api_manejo.post(
            "/api/animales/recintos",
            json={"nombre_recinto": unico("Recinto IT"), "tipo": "Jaula", "capacidad": 4},
        ),
        201,
    )


@pytest.fixture
def animal(api_manejo, taxonomia, recinto):
    """Un animal nuevo (con su propio recinto) para cada prueba: así no se cruzan horarios entre pruebas."""
    return exigir(
        api_manejo.post(
            "/api/animales",
            json={
                "id_taxonomia": taxonomia["id_taxonomia"],
                "id_recinto": recinto["id_recinto"],
                "nombre": unico("Yaku"),
                "edad_anios": 3,
                "edad_meses": 2,
                "sexo": "macho",
            },
        ),
        201,
    )


@pytest.fixture
def diagnostico(api_veterinaria, animal):
    return exigir(
        api_veterinaria.post(
            f"/api/animales/{animal['id_animal']}/diagnosticos",
            json={"diagnostico": "Infección respiratoria leve", "observaciones": "Control en una semana"},
        ),
        201,
    )


@pytest.fixture
def crear_tratamiento(api_veterinaria, diagnostico):
    """Fábrica de tratamientos del diagnóstico de la prueba. Devuelve la respuesta HTTP sin comprobarla."""

    def _crear(**cambios):
        datos = {
            "descripcion": "Antibiótico por tres días",
            "fecha_inicio": iso(en_dias(1)),
            "fecha_fin": iso(en_dias(3)),
            "frecuencia_valor": 1,
            "frecuencia_unidad": "dias",
            "hora_inicio": "09:00:00",
            "medicamentos": [
                {"nombre_medicamento": "Amoxicilina", "dosis_ml": 2.5},
                {"nombre_medicamento": "Vitamina B", "dosis_ml": 1},
            ],
        }
        datos.update(cambios)
        return api_veterinaria.post(
            f"/api/animales/diagnosticos/{diagnostico['id_diagnostico']}/tratamientos", json=datos
        )

    return _crear


# ---------- Actividades y dietas (con limpieza al terminar) ----------

@pytest.fixture
def programar(api_manejo):
    """Programa una actividad como Manejo de Animales y la elimina al terminar. Devuelve la respuesta HTTP."""
    creadas = []

    def _programar(datos: dict, **parametros):
        respuesta = api_manejo.post("/api/actividades", json=datos, params=parametros)
        if respuesta.status_code == 201:
            creadas.append(respuesta.json()["id_actividad"])
        return respuesta

    yield _programar
    for id_actividad in reversed(creadas):
        api_manejo.delete(f"/api/actividades/{id_actividad}")


@pytest.fixture
def crear_dieta(api_manejo):
    """Crea dietas y, al terminar, las finaliza (con eso se quitan sus tomas pendientes)."""
    creadas = []

    def _crear(id_animal: int, inicio=None, fin=None, valor: int = 1, unidad: str = "dias", **cambios):
        datos = {
            "id_animal": id_animal,
            "fecha_inicio": iso(inicio or en_dias(1)),
            "frecuencia_valor": valor,
            "frecuencia_unidad": unidad,
            "alimentos": [{"nombre_alimento": "Pollo", "cantidad_gramos": 250}],
        }
        if fin is not None:
            datos["fecha_fin"] = iso(fin)
        datos.update(cambios)
        respuesta = api_manejo.post("/api/actividades/dietas", json=datos)
        if respuesta.status_code == 201:
            creadas.append(respuesta.json()["id_dieta"])
        return respuesta

    yield _crear
    for id_dieta in creadas:
        api_manejo.post(f"/api/actividades/dietas/{id_dieta}/finalizar")


# ---------- Docker ----------

@pytest.fixture
def docker_requerido():
    if not docker_disponible():
        pytest.skip("Docker no está disponible")
    if id_contenedor("gateway") is None:
        pytest.skip("No se encontró el compose de pruebas en ejecución (proyecto yanacocha-test)")
