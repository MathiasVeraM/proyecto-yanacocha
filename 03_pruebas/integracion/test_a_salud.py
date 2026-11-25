"""a) Salud: /health y /health/ready de todos los servicios."""
import pytest

from ayudas import (
    PROYECTO_COMPOSE,
    PUERTO_INTERNO,
    contenedores_del_proyecto,
    estado_salud,
    get_dentro_del_contenedor,
)


def test_gateway_health_responde_sin_token(api_anonimo):
    respuesta = api_anonimo.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_gateway_solo_expone_liveness(api_anonimo):
    # Decisión de diseño: el gateway no tiene /health/ready, y /health no abre rutas nuevas
    assert api_anonimo.get("/health/ready").status_code == 404
    assert api_anonimo.get("/health/otra").status_code == 404


def test_health_del_gateway_no_revela_configuracion(api_anonimo):
    texto = api_anonimo.get("/health").text.lower()

    for dato in ("secret", "postgres", "http://", "password", "token"):
        assert dato not in texto


@pytest.mark.requiere_docker
@pytest.mark.parametrize("servicio", sorted(PUERTO_INTERNO))
def test_servicio_interno_health_liveness(docker_requerido, servicio):
    estado, cuerpo = get_dentro_del_contenedor(servicio, "/health")

    assert estado == 200
    assert '"status":"ok"' in cuerpo.replace(" ", "")


@pytest.mark.requiere_docker
@pytest.mark.parametrize("servicio", sorted(PUERTO_INTERNO))
def test_servicio_interno_health_ready_verifica_la_base(docker_requerido, servicio):
    estado, cuerpo = get_dentro_del_contenedor(servicio, "/health/ready")

    assert estado == 200
    assert '"status":"ready"' in cuerpo.replace(" ", "")


@pytest.mark.requiere_docker
@pytest.mark.parametrize("servicio", ["gateway", *sorted(PUERTO_INTERNO)])
def test_contenedor_reporta_estado_saludable(docker_requerido, servicio):
    assert estado_salud(servicio) == "healthy"


@pytest.mark.requiere_docker
def test_solo_el_gateway_publica_puertos_al_host(docker_requerido):
    publicados = {}
    for contenedor in contenedores_del_proyecto():
        servicio = contenedor["Config"]["Labels"]["com.docker.compose.service"]
        puertos = contenedor["NetworkSettings"]["Ports"] or {}
        enlazados = {puerto: enlaces for puerto, enlaces in puertos.items() if enlaces}
        if enlazados:
            publicados[servicio] = enlazados

    assert list(publicados) == ["gateway"], f"Puertos publicados en {PROYECTO_COMPOSE}: {publicados}"
    for enlaces in publicados["gateway"].values():
        assert all(enlace["HostIp"] in ("127.0.0.1", "::1") for enlace in enlaces)


@pytest.mark.requiere_docker
def test_contenedores_de_la_aplicacion_estan_endurecidos(docker_requerido):
    for contenedor in contenedores_del_proyecto():
        servicio = contenedor["Config"]["Labels"]["com.docker.compose.service"]
        config = contenedor["HostConfig"]
        assert "no-new-privileges:true" in (config["SecurityOpt"] or []), servicio
        assert "ALL" in (config["CapDrop"] or []), servicio
        # La base de datos de pruebas no usa ningún volumen: vive en memoria
        assert not [m for m in contenedor["Mounts"] if m["Type"] == "volume"], servicio
