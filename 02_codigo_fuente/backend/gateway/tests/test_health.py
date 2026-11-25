import pytest

from src.mapa_rutas import resolver_regla


def test_health_responde_sin_token(client_anonimo):
    respuesta = client_anonimo.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_health_no_llega_a_ningun_servicio(client_anonimo, servicio):
    client_anonimo.get("/health")

    assert servicio.peticiones == []


def test_health_no_expone_configuracion(client_anonimo):
    texto = client_anonimo.get("/health").text.lower()

    for dato in ("secret", "localhost", "http://", "token"):
        assert dato not in texto


def test_health_solo_acepta_get(client_anonimo):
    assert client_anonimo.post("/health").status_code == 405
    assert client_anonimo.delete("/health").status_code == 405


def test_health_no_se_agrega_al_mapa_de_rutas():
    # El mapa sigue fallando cerrado: /health se atiende en el gateway y nunca se autoriza como ruta proxy
    assert resolver_regla("GET", "/health") is None


@pytest.mark.parametrize("ruta", ["/health/ready", "/health/otra", "/healthz", "/api/health"])
def test_otras_rutas_de_salud_no_existen(client_anonimo, servicio, ruta):
    assert client_anonimo.get(ruta).status_code == 404
    assert servicio.peticiones == []


@pytest.mark.parametrize(
    "ruta", ["/api/auth/health", "/api/animales/health", "/api/actividades/health"]
)
def test_health_bajo_un_servicio_sigue_exigiendo_token(client_anonimo, servicio, ruta):
    # Que exista /health en el gateway no abre /health de los servicios a través del proxy
    assert client_anonimo.get(ruta).status_code == 401
    assert servicio.peticiones == []


def test_health_bajo_un_servicio_con_token_se_reenvia_como_cualquier_ruta(client, servicio):
    respuesta = client.get("/api/actividades/health")

    assert respuesta.status_code == 200
    assert str(servicio.ultima.url).endswith("/api/actividades/health")
