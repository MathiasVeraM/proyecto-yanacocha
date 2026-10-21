"""Subida y descarga de la fotografía del ejemplar."""
import pytest

from src.logica_negocio.imagen_service import TAMANO_MAXIMO, detectar_tipo

URL = "/api/animales"

# Solo importa la firma de los primeros bytes: el servicio detecta el tipo por el contenido
PNG = b"\x89PNG\r\n\x1a\n" + b"datos-png"
JPG = b"\xff\xd8\xff\xe0" + b"datos-jpg"
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"datos-webp"


@pytest.fixture
def h(headers_con_permiso):
    return headers_con_permiso


@pytest.fixture
def animal(crear_animal_db):
    return crear_animal_db()


def _subir(client, h, id_animal, contenido, nombre="foto.png", tipo="image/png"):
    return client.put(f"{URL}/{id_animal}/imagen", files={"archivo": (nombre, contenido, tipo)}, headers=h)


@pytest.mark.parametrize("contenido,esperado", [
    (PNG, "image/png"),
    (JPG, "image/jpeg"),
    (WEBP, "image/webp"),
    (b"GIF89a...", None),
    (b"%PDF-1.7", None),
    (b"", None),
])
def test_detectar_tipo_por_contenido(contenido, esperado):
    assert detectar_tipo(contenido) == esperado


def test_subir_foto_actualiza_url_imagen(client, h, animal):
    resp = _subir(client, h, animal.id_animal, PNG)

    assert resp.status_code == 200
    url = resp.json()["url_imagen"]
    assert url.startswith(f"{URL}/{animal.id_animal}/imagen?v=")


def test_descargar_foto_devuelve_el_mismo_archivo(client, h, animal):
    _subir(client, h, animal.id_animal, JPG, nombre="foto.jpg", tipo="image/jpeg")

    resp = client.get(f"{URL}/{animal.id_animal}/imagen", headers=h)

    assert resp.status_code == 200
    assert resp.content == JPG
    assert resp.headers["content-type"] == "image/jpeg"
    assert "max-age" in resp.headers["cache-control"]


def test_subir_otra_foto_reemplaza_la_anterior(client, h, animal):
    _subir(client, h, animal.id_animal, PNG)
    _subir(client, h, animal.id_animal, WEBP, nombre="nueva.webp", tipo="image/webp")

    resp = client.get(f"{URL}/{animal.id_animal}/imagen", headers=h)

    assert resp.content == WEBP
    assert resp.headers["content-type"] == "image/webp"


def test_el_tipo_se_decide_por_el_contenido_y_no_por_la_extension(client, h, animal):
    # Un PDF renombrado a .png y declarado como image/png se rechaza
    resp = _subir(client, h, animal.id_animal, b"%PDF-1.7 ...", nombre="foto.png", tipo="image/png")
    assert resp.status_code == 415
    assert resp.json()["detail"] == "La fotografía debe ser una imagen JPG, PNG o WEBP"


def test_foto_demasiado_grande_413(client, h, animal):
    grande = PNG + b"0" * TAMANO_MAXIMO
    resp = _subir(client, h, animal.id_animal, grande)
    assert resp.status_code == 413
    # No se guardó nada
    assert client.get(f"{URL}/{animal.id_animal}/imagen", headers=h).status_code == 404


def test_foto_justo_en_el_limite_se_acepta(client, h, animal):
    exacta = PNG + b"0" * (TAMANO_MAXIMO - len(PNG))
    assert _subir(client, h, animal.id_animal, exacta).status_code == 200


def test_subir_sin_archivo_422(client, h, animal):
    assert client.put(f"{URL}/{animal.id_animal}/imagen", headers=h).status_code == 422


def test_subir_foto_a_animal_inexistente_404(client, h):
    assert _subir(client, h, 999, PNG).status_code == 404


def test_animal_sin_foto_404(client, h, animal):
    resp = client.get(f"{URL}/{animal.id_animal}/imagen", headers=h)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "El animal no tiene fotografía"


def test_foto_de_animal_inexistente_404(client, h):
    assert client.get(f"{URL}/999/imagen", headers=h).status_code == 404


def test_url_imagen_no_se_puede_escribir_a_mano(client, h, animal):
    resp = client.put(f"{URL}/{animal.id_animal}", json={"url_imagen": "https://otro-sitio/x.png"}, headers=h)
    assert resp.status_code == 200
    assert resp.json()["url_imagen"] is None


@pytest.mark.parametrize("metodo", ["GET", "PUT"])
def test_foto_exige_token_y_permiso(client, headers_sin_permiso, animal, metodo):
    url = f"{URL}/{animal.id_animal}/imagen"
    assert client.request(metodo, url).status_code == 401
    assert client.request(metodo, url, headers=headers_sin_permiso).status_code == 403
