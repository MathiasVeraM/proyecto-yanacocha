"""Pruebas del reenvío de /api/animales/* al servicio de gestión animal (con el servicio simulado)."""
import httpx
import pytest

from src.config import GESTION_ANIMAL_SERVICE_URL
from src.modulos import MODULO_ACCESOS, MODULO_FICHAS_EJEMPLARES
from src.rutas.gestion_animal_router import URL_DESTINO


# ---- Reenvío de la petición ----

@pytest.mark.parametrize("metodo", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_reenvia_cada_metodo_permitido(client, servicio, metodo):
    response = client.request(metodo, "/api/animales/5/diagnosticos")

    assert response.status_code == 200
    assert servicio.ultima.method == metodo
    assert str(servicio.ultima.url) == f"{URL_DESTINO}/5/diagnosticos"


@pytest.mark.parametrize("metodo", ["GET", "POST"])
def test_raiz_del_prefijo_se_reenvia_sin_barra_final(client, servicio, metodo):
    # El listado y el registro de animales viven en /api/animales, sin "/" al final
    client.request(metodo, "/api/animales")

    assert str(servicio.ultima.url) == f"{GESTION_ANIMAL_SERVICE_URL}/api/animales"


def test_url_destino_apunta_al_servicio_de_gestion_animal():
    assert URL_DESTINO == f"{GESTION_ANIMAL_SERVICE_URL}/api/animales"


def test_reenvia_el_cuerpo(client, servicio):
    animal = {"codigo_animal": "YNC-001", "nombre_comun": "Oso de anteojos"}

    client.post("/api/animales", json=animal)

    assert servicio.ultima.read() == httpx.Request("POST", "http://x", json=animal).read()


def test_reenvia_el_token_de_autorizacion(client, servicio, headers_admin):
    # El servicio necesita el token para saber quién registra cada diagnóstico
    client.get("/api/animales/1")

    assert servicio.ultima.headers["authorization"] == headers_admin["Authorization"]


def test_respeta_el_codigo_de_estado_del_servicio(client, servicio):
    servicio.respuesta = httpx.Response(409, json={"detail": "El animal tiene diagnósticos"})

    response = client.delete("/api/animales/1")

    assert response.status_code == 409
    assert response.json() == {"detail": "El animal tiene diagnósticos"}


def test_bloquea_path_traversal_sin_llamar_al_servicio(client, servicio):
    response = client.get("/api/animales/%2e%2e/%2e%2e/api/auth/usuarios")

    assert response.status_code == 400
    assert servicio.peticiones == []


def test_servicio_caido_devuelve_503_con_su_nombre(client, servicio):
    servicio.error = httpx.ConnectError("conexión rechazada")

    response = client.get("/api/animales")

    assert response.status_code == 503
    assert response.json() == {"detail": "El servicio de gestión animal no está disponible"}


def test_servicio_lento_devuelve_504_con_su_nombre(client, servicio):
    servicio.error = httpx.ReadTimeout("tiempo agotado")

    response = client.get("/api/animales")

    assert response.status_code == 504
    assert response.json() == {"detail": "El servicio de gestión animal no respondió a tiempo"}


# ---- Control de acceso ----

@pytest.mark.parametrize("ruta", ["/api/animales", "/api/animales/1/diagnosticos"])
def test_sin_token_401_y_no_llega_al_servicio(client_anonimo, servicio, ruta):
    response = client_anonimo.get(ruta)

    assert response.status_code == 401
    assert servicio.peticiones == []


@pytest.mark.parametrize("ruta", ["/api/animales", "/api/animales/1"])
def test_rol_sin_el_modulo_403(client_anonimo, servicio, crear_token, cabeceras, ruta):
    # Tener permiso sobre otro módulo no da acceso a gestión animal
    token = crear_token(modulos=[MODULO_ACCESOS])

    response = client_anonimo.get(ruta, headers=cabeceras(token))

    assert response.status_code == 403
    assert servicio.peticiones == []


@pytest.mark.parametrize("ruta", ["/api/animales", "/api/animales/1/diagnosticos"])
def test_rol_con_el_modulo_pasa(client_anonimo, servicio, crear_token, cabeceras, ruta):
    token = crear_token(modulos=[MODULO_FICHAS_EJEMPLARES])

    response = client_anonimo.get(ruta, headers=cabeceras(token))

    assert response.status_code == 200
    assert len(servicio.peticiones) == 1


def test_permiso_de_gestion_animal_no_abre_accesos(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(modulos=[MODULO_FICHAS_EJEMPLARES])

    response = client_anonimo.get("/api/auth/usuarios", headers=cabeceras(token))

    assert response.status_code == 403
    assert servicio.peticiones == []
