"""Endpoints de taxonomía (catálogo + iNaturalist simulado) y de recintos."""
import httpx2
import pytest

from src.modelos.fechas import hoy_local

URL_TAX = "/api/animales/taxonomia"
URL_REC = "/api/animales/recintos"

OSO_INAT = {
    "id": 41657,
    "name": "Tremarctos ornatus",
    "rank": "species",
    "preferred_common_name": "Oso de Anteojos",
    "ancestor_ids": [48460, 1, 2, 355675, 40151, 848317, 41636, 41656, 41657],
    "ancestors": [
        {"rank": "class", "name": "Mammalia"},
        {"rank": "family", "name": "Ursidae"},
        {"rank": "genus", "name": "Tremarctos"},
    ],
}
GENERO_INAT = {"id": 41656, "name": "Tremarctos", "rank": "genus", "ancestor_ids": [48460, 1, 41656]}
PLANTA_INAT = {"id": 5, "name": "Rosa multiflora", "rank": "species", "ancestor_ids": [48460, 47126, 5]}


@pytest.fixture
def h(headers_con_permiso):
    return headers_con_permiso


# ---------- Catálogo propio ----------

def test_crear_y_listar_especies(client, h):
    resp = client.post(
        URL_TAX,
        json={"nombre_comun": " Perro ", "especie": "Canis lupus familiaris", "genero": "Canis", "familia": "Canidae"},
        headers=h,
    )
    assert resp.status_code == 201
    assert resp.json()["nombre_comun"] == "Perro" and resp.json()["id_inaturalist"] is None

    assert [t["nombre_comun"] for t in client.get(URL_TAX, headers=h).json()] == ["Perro"]
    assert client.get(URL_TAX, params={"buscar": "canis"}, headers=h).json()[0]["nombre_comun"] == "Perro"
    assert client.get(URL_TAX, params={"buscar": "gato"}, headers=h).json() == []


def test_crear_especie_nombre_comun_repetido_400(client, h, crear_taxonomia_db):
    crear_taxonomia_db(nombre_comun="Perro", especie="Canis lupus familiaris")
    resp = client.post(URL_TAX, json={"nombre_comun": "PERRO", "especie": "Otra cosa"}, headers=h)
    assert resp.status_code == 400


def test_crear_especie_sin_letras_400(client, h):
    resp = client.post(URL_TAX, json={"nombre_comun": "Raro", "especie": "123"}, headers=h)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "El nombre científico debe contener letras"


@pytest.mark.parametrize("cuerpo", [{"nombre_comun": "X"}, {"especie": "X y"}, {"nombre_comun": "", "especie": "X"}])
def test_crear_especie_datos_incompletos_422(client, h, cuerpo):
    assert client.post(URL_TAX, json=cuerpo, headers=h).status_code == 422


def test_actualizar_especie(client, h, crear_taxonomia_db):
    t = crear_taxonomia_db(nombre_comun="Perro", especie="Canis familiaris")
    resp = client.put(f"{URL_TAX}/{t.id_taxonomia}", json={"especie": "Canis lupus familiaris"}, headers=h)
    assert resp.status_code == 200 and resp.json()["especie"] == "Canis lupus familiaris"


def test_actualizar_especie_mismo_nombre_con_otras_mayusculas_200(client, h, crear_taxonomia_db):
    t = crear_taxonomia_db(nombre_comun="Perro", especie="Canis familiaris")
    resp = client.put(f"{URL_TAX}/{t.id_taxonomia}", json={"nombre_comun": "perro"}, headers=h)
    assert resp.status_code == 200 and resp.json()["nombre_comun"] == "perro"


def test_actualizar_especie_a_nombre_de_otra_400(client, h, crear_taxonomia_db):
    crear_taxonomia_db(nombre_comun="Perro", especie="Canis familiaris")
    gato = crear_taxonomia_db(nombre_comun="Gato", especie="Felis catus")
    assert client.put(f"{URL_TAX}/{gato.id_taxonomia}", json={"nombre_comun": "perro"}, headers=h).status_code == 400


def test_actualizar_especie_sin_letras_400(client, h, crear_taxonomia_db):
    t = crear_taxonomia_db()
    assert client.put(f"{URL_TAX}/{t.id_taxonomia}", json={"especie": "1 2"}, headers=h).status_code == 400


def test_actualizar_especie_inexistente_404(client, h):
    assert client.put(f"{URL_TAX}/999", json={"familia": "X"}, headers=h).status_code == 404


# ---------- Sugerencias (catálogo + iNaturalist) ----------

def test_sugerencias_combinan_catalogo_e_inaturalist(client, h, crear_taxonomia_db, inaturalist_simulado):
    crear_taxonomia_db(nombre_comun="Oso hormiguero", especie="Myrmecophaga tridactyla")
    inaturalist_simulado.responder("/taxa/autocomplete", {"results": [OSO_INAT]})

    resp = client.get(f"{URL_TAX}/sugerencias", params={"buscar": "oso"}, headers=h)

    assert resp.status_code == 200
    assert resp.json() == [
        {"origen": "catalogo", "id_taxonomia": 1, "id_inaturalist": None,
         "nombre_comun": "Oso hormiguero", "especie": "Myrmecophaga tridactyla"},
        {"origen": "inaturalist", "id_taxonomia": None, "id_inaturalist": 41657,
         "nombre_comun": "Oso de Anteojos", "especie": "Tremarctos ornatus"},
    ]
    # Se pide en español y solo animales
    params = inaturalist_simulado.peticiones[0].url.params
    assert (params["q"], params["locale"], params["taxon_id"]) == ("oso", "es", "1")


def test_sugerencias_descarta_generos_y_plantas(client, h, inaturalist_simulado):
    inaturalist_simulado.responder("/taxa/autocomplete", {"results": [GENERO_INAT, PLANTA_INAT, OSO_INAT]})
    resp = client.get(f"{URL_TAX}/sugerencias", params={"buscar": "tre"}, headers=h)
    assert [s["especie"] for s in resp.json()] == ["Tremarctos ornatus"]


def test_sugerencias_no_repite_lo_ya_importado(client, h, crear_taxonomia_db, inaturalist_simulado):
    crear_taxonomia_db(nombre_comun="Oso de Anteojos", especie="Tremarctos ornatus", id_inaturalist=41657)
    inaturalist_simulado.responder("/taxa/autocomplete", {"results": [OSO_INAT]})
    resp = client.get(f"{URL_TAX}/sugerencias", params={"buscar": "oso"}, headers=h)
    assert [s["origen"] for s in resp.json()] == ["catalogo"]


@pytest.mark.parametrize("error", [httpx2.ConnectError("sin internet"), httpx2.ReadTimeout("lento")])
def test_sugerencias_sin_inaturalist_devuelve_solo_el_catalogo(client, h, crear_taxonomia_db, inaturalist_simulado, error):
    crear_taxonomia_db(nombre_comun="Oso de anteojos", especie="Tremarctos ornatus")
    inaturalist_simulado.error = error
    resp = client.get(f"{URL_TAX}/sugerencias", params={"buscar": "oso"}, headers=h)
    assert resp.status_code == 200
    assert [s["origen"] for s in resp.json()] == ["catalogo"]


def test_sugerencias_con_inaturalist_respondiendo_error_devuelve_solo_el_catalogo(client, h, inaturalist_simulado):
    inaturalist_simulado.responder("/taxa/autocomplete", {"error": "caído"}, codigo=500)
    assert client.get(f"{URL_TAX}/sugerencias", params={"buscar": "oso"}, headers=h).json() == []


def test_sugerencias_exigen_al_menos_dos_letras(client, h):
    assert client.get(f"{URL_TAX}/sugerencias", params={"buscar": "o"}, headers=h).status_code == 422


# ---------- Importar desde iNaturalist ----------

def test_importar_guarda_la_especie_con_genero_y_familia(client, h, inaturalist_simulado):
    inaturalist_simulado.responder("/taxa/41657", {"results": [OSO_INAT]})

    resp = client.post(f"{URL_TAX}/importar", json={"id_inaturalist": 41657}, headers=h)

    assert resp.status_code == 200
    assert {k: resp.json()[k] for k in ("nombre_comun", "especie", "genero", "familia", "id_inaturalist")} == {
        "nombre_comun": "Oso de Anteojos", "especie": "Tremarctos ornatus",
        "genero": "Tremarctos", "familia": "Ursidae", "id_inaturalist": 41657,
    }
    # Queda en el catálogo
    assert client.get(URL_TAX, headers=h).json()[0]["especie"] == "Tremarctos ornatus"


def test_importar_dos_veces_devuelve_la_misma_sin_llamar_a_inaturalist(client, h, crear_taxonomia_db, inaturalist_simulado):
    existente = crear_taxonomia_db(id_inaturalist=41657)
    resp = client.post(f"{URL_TAX}/importar", json={"id_inaturalist": 41657}, headers=h)
    assert resp.json()["id_taxonomia"] == existente.id_taxonomia
    assert inaturalist_simulado.peticiones == []


def test_importar_sin_nombre_comun_usa_el_cientifico(client, h, inaturalist_simulado):
    sin_nombre = {**OSO_INAT, "preferred_common_name": None}
    inaturalist_simulado.responder("/taxa/41657", {"results": [sin_nombre]})
    resp = client.post(f"{URL_TAX}/importar", json={"id_inaturalist": 41657}, headers=h)
    assert resp.json()["nombre_comun"] == "Tremarctos ornatus"


def test_importar_nombre_comun_ya_usado_400(client, h, crear_taxonomia_db, inaturalist_simulado):
    crear_taxonomia_db(nombre_comun="oso de anteojos", especie="Tremarctos ornatus")
    inaturalist_simulado.responder("/taxa/41657", {"results": [OSO_INAT]})
    assert client.post(f"{URL_TAX}/importar", json={"id_inaturalist": 41657}, headers=h).status_code == 400


@pytest.mark.parametrize("respuesta", [{"results": []}, {"results": [GENERO_INAT]}, {"results": [PLANTA_INAT]}])
def test_importar_inexistente_o_no_animal_404(client, h, inaturalist_simulado, respuesta):
    inaturalist_simulado.responder("/taxa/5", respuesta)
    assert client.post(f"{URL_TAX}/importar", json={"id_inaturalist": 5}, headers=h).status_code == 404


@pytest.mark.parametrize("error", [httpx2.ConnectError("sin internet"), httpx2.ReadTimeout("lento")])
def test_importar_sin_inaturalist_503(client, h, inaturalist_simulado, error):
    inaturalist_simulado.error = error
    resp = client.post(f"{URL_TAX}/importar", json={"id_inaturalist": 41657}, headers=h)
    assert resp.status_code == 503


def test_importar_id_invalido_422(client, h):
    assert client.post(f"{URL_TAX}/importar", json={"id_inaturalist": 0}, headers=h).status_code == 422


def test_la_especie_importada_sirve_para_registrar_un_animal(client, h, crear_recinto_db, inaturalist_simulado):
    inaturalist_simulado.responder("/taxa/41657", {"results": [OSO_INAT]})
    especie = client.post(f"{URL_TAX}/importar", json={"id_inaturalist": 41657}, headers=h).json()
    recinto = crear_recinto_db()

    animal = client.post(
        "/api/animales",
        json={"id_taxonomia": especie["id_taxonomia"], "id_recinto": recinto.id_recinto},
        headers=h,
    ).json()

    assert animal["codigo_animal"] == f"YC-{hoy_local().year}-0001"


def test_actualizar_animal_con_taxonomia_importada_de_inaturalist(
    client, h, crear_recinto_db, inaturalist_simulado
):
    inaturalist_simulado.responder("/taxa/41657", {"results": [OSO_INAT]})
    oso = client.post(f"{URL_TAX}/importar", json={"id_inaturalist": 41657}, headers=h).json()
    recinto = crear_recinto_db()
    animal = client.post(
        "/api/animales",
        json={"id_taxonomia": oso["id_taxonomia"], "id_recinto": recinto.id_recinto},
        headers=h,
    ).json()

    condor_inat = {
        **OSO_INAT,
        "id": 12345,
        "name": "Vultur gryphus",
        "preferred_common_name": "Cóndor andino",
        "ancestor_ids": [1, 2, 3],
        "ancestors": [
            {"rank": "class", "name": "Aves"},
            {"rank": "family", "name": "Cathartidae"},
            {"rank": "genus", "name": "Vultur"},
        ],
    }
    inaturalist_simulado.responder("/taxa/12345", {"results": [condor_inat]})
    condor = client.post(f"{URL_TAX}/importar", json={"id_inaturalist": 12345}, headers=h).json()

    resp = client.put(
        f"/api/animales/{animal['id_animal']}",
        json={"id_taxonomia": condor["id_taxonomia"]},
        headers=h,
    )

    assert resp.status_code == 200
    assert resp.json()["codigo_animal"] == animal["codigo_animal"]
    assert resp.json()["taxonomia"]["nombre_comun"] == "Cóndor andino"
    assert resp.json()["taxonomia"]["id_inaturalist"] == 12345


# ---------- Recintos ----------

def test_crear_y_listar_recintos(client, h):
    resp = client.post(URL_REC, json={"nombre_recinto": "Aviario", "tipo": "aviario", "capacidad": 8}, headers=h)
    assert resp.status_code == 201
    assert resp.json()["estado"] == "disponible"
    client.post(URL_REC, json={"nombre_recinto": "Aaa cuarentena"}, headers=h)
    assert [r["nombre_recinto"] for r in client.get(URL_REC, headers=h).json()] == ["Aaa cuarentena", "Aviario"]


def test_crear_recinto_nombre_repetido_400(client, h, crear_recinto_db):
    crear_recinto_db(nombre_recinto="Aviario")
    assert client.post(URL_REC, json={"nombre_recinto": "Aviario"}, headers=h).status_code == 400


@pytest.mark.parametrize("cuerpo", [
    {"nombre_recinto": ""},
    {"nombre_recinto": "X", "capacidad": 0},
    {"nombre_recinto": "X", "estado": "cerrado"},
])
def test_crear_recinto_datos_invalidos_422(client, h, cuerpo):
    assert client.post(URL_REC, json=cuerpo, headers=h).status_code == 422


def test_actualizar_recinto(client, h, crear_recinto_db):
    r = crear_recinto_db(nombre_recinto="Aviario")
    resp = client.put(f"{URL_REC}/{r.id_recinto}", json={"estado": "en_mantenimiento", "nombre_recinto": "Aviario"}, headers=h)
    assert resp.status_code == 200 and resp.json()["estado"] == "en_mantenimiento"


def test_actualizar_recinto_a_nombre_de_otro_400(client, h, crear_recinto_db):
    crear_recinto_db(nombre_recinto="Aviario")
    r = crear_recinto_db(nombre_recinto="Terrario")
    assert client.put(f"{URL_REC}/{r.id_recinto}", json={"nombre_recinto": "Aviario"}, headers=h).status_code == 400


def test_actualizar_recinto_inexistente_404(client, h):
    assert client.put(f"{URL_REC}/999", json={"tipo": "X"}, headers=h).status_code == 404


def test_rutas_de_catalogos_no_chocan_con_las_de_animales(client, h):
    # /api/animales/recintos no debe interpretarse como /api/animales/{id_animal}
    assert client.get(URL_REC, headers=h).status_code == 200
    assert client.get(URL_TAX, headers=h).status_code == 200
