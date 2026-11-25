"""Utilidades compartidas por las pruebas de integración (fechas, clientes HTTP, docker)."""
import json
import os
import subprocess
import time
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

# La base de datos está en UTC, pero los servicios calculan "hoy" en esta zona. Las pruebas hacen lo mismo.
ZONA = ZoneInfo("America/Guayaquil")

# id_rol de la tabla rol (los inserta gestion_usuarios.sql)
ROL_ADMIN = 1
ROL_VETERINARIA = 2
ROL_MANEJO = 3
ROL_VOLUNTARIO = 4

# Dominio de todos los correos de prueba. No puede ser .test: el validador de correos de Accesos lo rechaza.
DOMINIO_CORREOS = "pruebas-yanacocha.com"

PROYECTO_COMPOSE = os.environ.get("COMPOSE_PROJECT_NAME", "yanacocha-test")
PUERTO_INTERNO = {"accesos": 8001, "gestion-animal": 8002, "actividades": 8003}


# ---------- Fechas (siempre en hora de Ecuador) ----------

def ahora_ec() -> datetime:
    return datetime.now(ZONA)


def hoy_ec() -> date:
    return ahora_ec().date()


def en_dias(dias: int) -> date:
    return hoy_ec() + timedelta(days=dias)


def iso(fecha: date) -> str:
    return fecha.isoformat()


def unico(prefijo: str) -> str:
    """Nombre único para no chocar con otras pruebas (ni con otros procesos en paralelo)."""
    return f"{prefijo}-{uuid.uuid4().hex[:8]}"


# ---------- HTTP ----------

def url_gateway() -> str:
    return os.environ.get("GATEWAY_URL", "http://127.0.0.1:8000").rstrip("/")


def crear_cliente(token: str | None = None) -> httpx.Client:
    cabeceras = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.Client(base_url=url_gateway(), headers=cabeceras, timeout=30.0)


def exigir(respuesta: httpx.Response, codigo: int = 200):
    """Comprueba el código de estado (con el cuerpo en el mensaje) y devuelve el JSON, si lo hay."""
    assert respuesta.status_code == codigo, (
        f"{respuesta.request.method} {respuesta.request.url.path} -> "
        f"{respuesta.status_code} (se esperaba {codigo}): {respuesta.text[:500]}"
    )
    return respuesta.json() if respuesta.content else None


# ---------- Datos de prueba ----------

def datos_limpieza(id_recinto: int, fecha: date, hora: str | None = None, minutos: int = 30) -> dict:
    datos = {
        "tipo_actividad": "limpieza",
        "id_recinto": id_recinto,
        "fecha_programada": iso(fecha),
        "duracion_horas": minutos // 60,
        "duracion_minutos": minutos % 60,
    }
    if hora:
        datos["hora_programada"] = hora
    return datos


def datos_enriquecimiento(id_animal: int, fecha: date, hora: str = "10:00", **extra) -> dict:
    return {
        "tipo_actividad": "enriquecimiento",
        "id_animal": id_animal,
        "fecha_programada": iso(fecha),
        "hora_programada": hora,
        "tipo_enriquecimiento": "sensorial",
        "descripcion_estimulo": "Esconder fruta en el recinto",
        **extra,
    }


def datos_entrenamiento(id_animal: int, fecha: date, hora: str = "11:00", minutos: int = 60) -> dict:
    return {
        "tipo_actividad": "entrenamiento",
        "id_animal": id_animal,
        "fecha_programada": iso(fecha),
        "hora_programada": hora,
        "duracion_horas": minutos // 60,
        "duracion_minutos": minutos % 60,
        "objetivo_entrenamiento": "Entrar al transportador",
        "tipo_refuerzo": "Alimento",
    }


# ---------- Docker (solo para pruebas marcadas con requiere_docker) ----------

def _docker(*argumentos: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *argumentos], capture_output=True, text=True, timeout=timeout)


def docker_disponible() -> bool:
    try:
        return _docker("info", "--format", "{{.ServerVersion}}", timeout=15).returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def id_contenedor(servicio: str) -> str | None:
    salida = _docker(
        "ps", "-aq",
        "--filter", f"label=com.docker.compose.project={PROYECTO_COMPOSE}",
        "--filter", f"label=com.docker.compose.service={servicio}",
    ).stdout.split()
    return salida[0] if salida else None


def contenedores_del_proyecto() -> list[dict]:
    ids = _docker(
        "ps", "-aq", "--filter", f"label=com.docker.compose.project={PROYECTO_COMPOSE}"
    ).stdout.split()
    if not ids:
        return []
    return json.loads(_docker("inspect", *ids).stdout)


def get_dentro_del_contenedor(servicio: str, ruta: str) -> tuple[int, str]:
    """GET a un servicio interno (que no publica puerto) ejecutando Python dentro de su propio contenedor."""
    url = f"http://127.0.0.1:{PUERTO_INTERNO[servicio]}{ruta}"
    codigo = (
        "import urllib.request, urllib.error\n"
        "try:\n"
        f"    r = urllib.request.urlopen({url!r}, timeout=5)\n"
        "    print(r.status); print(r.read().decode())\n"
        "except urllib.error.HTTPError as e:\n"
        "    print(e.code); print(e.read().decode())\n"
    )
    resultado = _docker("exec", id_contenedor(servicio), "python", "-c", codigo)
    assert resultado.returncode == 0, resultado.stderr
    estado, _, cuerpo = resultado.stdout.partition("\n")
    return int(estado), cuerpo.strip()


def estado_salud(servicio: str) -> str:
    salida = _docker("inspect", "-f", "{{.State.Health.Status}}", id_contenedor(servicio)).stdout.strip()
    return salida or "sin-healthcheck"


def detener_contenedor(servicio: str) -> None:
    _docker("stop", "-t", "5", id_contenedor(servicio))


def iniciar_contenedor(servicio: str, segundos: int = 90) -> None:
    """Arranca el contenedor y espera a que su healthcheck lo marque como saludable."""
    _docker("start", id_contenedor(servicio))
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        if estado_salud(servicio) == "healthy":
            return
        time.sleep(1)
    raise AssertionError(f"El servicio {servicio} no volvió a estar saludable en {segundos} s")
