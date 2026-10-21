"""Clase y orden taxonómicos (desde iNaturalist o a mano) y nombre propio del ejemplar."""
import pytest

URL = "/api/animales"

OSO_INAT = {
    "id": 41657,
    "name": "Tremarctos ornatus",
    "rank": "species",
    "preferred_common_name": "Oso de Anteojos",
    "ancestor_ids": [48460, 1, 2, 355675, 40151, 848317, 41636, 41656, 41657],
    "ancestors": [
        {"rank": "kingdom", "name": "Animalia"},
        {"rank": "class", "name": "Mammalia"},
        {"rank": "order", "name": "Carnivora"},
        {"rank": "family", "name": "Ursidae"},
        {"rank": "genus", "name": "Tremarctos"},
    ],
}


@pytest.fixture
def h(headers_con_permiso):
    return headers_con_permiso


def test_importar_de_inaturalist_llena_clase_y_orden(client, h, inaturalist_simulado):
    inaturalist_simulado.responder("/taxa/41657", {"results": [OSO_INAT]})

    especie = client.post(f"{URL}/taxonomia/importar", json={"id_inaturalist": 41657}, headers=h).json()

    assert (especie["clase"], especie["orden"]) == ("Mammalia", "Carnivora")


def test_especie_manual_con_clase_y_orden(client, h):
    resp = client.post(
        f"{URL}/taxonomia",
        json={"nombre_comun": "Caimán de anteojos", "especie": "Caiman crocodilus",
              "clase": "Reptilia", "orden": "Crocodylia"},
        headers=h,
    )
    assert resp.status_code == 201
    assert (resp.json()["clase"], resp.json()["orden"]) == ("Reptilia", "Crocodylia")


def test_corregir_clase_de_una_especie(client, h, crear_taxonomia_db):
    t = crear_taxonomia_db()
    resp = client.put(f"{URL}/taxonomia/{t.id_taxonomia}", json={"clase": "Mammalia"}, headers=h)
    assert resp.json()["clase"] == "Mammalia"


def test_registrar_animal_con_nombre_propio(client, h, crear_taxonomia_db, crear_recinto_db):
    t = crear_taxonomia_db(clase="Mammalia", orden="Carnivora")
    r = crear_recinto_db()

    animal = client.post(
        URL, json={"id_taxonomia": t.id_taxonomia, "id_recinto": r.id_recinto, "nombre": " Yaku "}, headers=h
    ).json()

    assert animal["nombre"] == "Yaku"
    # La ficha trae la clase y el orden desde la taxonomía
    assert (animal["taxonomia"]["clase"], animal["taxonomia"]["orden"]) == ("Mammalia", "Carnivora")


def test_el_nombre_propio_es_opcional_y_editable(client, h, crear_animal_db):
    animal = crear_animal_db()
    assert client.get(f"{URL}/{animal.id_animal}", headers=h).json()["nombre"] is None

    resp = client.put(f"{URL}/{animal.id_animal}", json={"nombre": "Kusi"}, headers=h)
    assert resp.json()["nombre"] == "Kusi"


@pytest.fixture
def animales_de_varias_clases(crear_taxonomia_db, crear_recinto_db, crear_animal_db):
    oso = crear_taxonomia_db(nombre_comun="Oso de anteojos", especie="Tremarctos ornatus", clase="Mammalia")
    condor = crear_taxonomia_db(nombre_comun="Cóndor andino", especie="Vultur gryphus", clase="Aves")
    recinto = crear_recinto_db()
    crear_animal_db(codigo_animal="TO-001", nombre="Yaku", id_taxonomia=oso.id_taxonomia, id_recinto=recinto.id_recinto)
    crear_animal_db(codigo_animal="VG-001", nombre="Inti", id_taxonomia=condor.id_taxonomia, id_recinto=recinto.id_recinto)


def _codigos(resp):
    assert resp.status_code == 200, resp.text
    return [a["codigo_animal"] for a in resp.json()]


def test_filtrar_animales_por_clase(client, h, animales_de_varias_clases):
    assert _codigos(client.get(URL, params={"clase": "Aves"}, headers=h)) == ["VG-001"]
    assert _codigos(client.get(URL, params={"clase": "Mammalia"}, headers=h)) == ["TO-001"]
    assert _codigos(client.get(URL, params={"clase": "Reptilia"}, headers=h)) == []


def test_buscar_por_nombre_propio(client, h, animales_de_varias_clases):
    assert _codigos(client.get(URL, params={"buscar": "yak"}, headers=h)) == ["TO-001"]


def test_clase_y_texto_combinados(client, h, animales_de_varias_clases):
    resp = client.get(URL, params={"clase": "Mammalia", "buscar": "inti"}, headers=h)
    assert _codigos(resp) == []
