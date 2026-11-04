"""Asume POST/GET /api/actividades/enriquecimientos."""

import pytest


def _cuerpo_enriquecimiento(animal_id, **extra):
    return {
        "id_animal": animal_id,
        "tipo_enriquecimiento": "sensorial",
        "fecha_programada": "2026-05-10",
        "hora_programada": "10:00:00",
        "descripcion_estimulo": "Ramas frescas con hojas",
        **extra,
    }


def test_programar_enriquecimiento_con_estimulo(client, animal_prueba):
    respuesta = client.post(
        "/api/actividades/enriquecimientos",
        json=_cuerpo_enriquecimiento(animal_prueba["id_animal"]),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["id_animal"] == animal_prueba["id_animal"]
    assert respuesta.json()["tipo_enriquecimiento"] == "sensorial"
    assert respuesta.json()["descripcion_estimulo"] == "Ramas frescas con hojas"


@pytest.mark.parametrize("tipo", ["social", "sensorial", "alimenticio", "cognitivo"])
def test_aceptar_tipos_de_enriquecimiento(client, animal_prueba, tipo):
    respuesta = client.post(
        "/api/actividades/enriquecimientos",
        json=_cuerpo_enriquecimiento(animal_prueba["id_animal"], tipo_enriquecimiento=tipo),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["tipo_enriquecimiento"] == tipo


def test_rechazar_tipo_de_enriquecimiento_invalido(client, animal_prueba):
    respuesta = client.post(
        "/api/actividades/enriquecimientos",
        json=_cuerpo_enriquecimiento(animal_prueba["id_animal"], tipo_enriquecimiento="olfativo"),
    )

    assert respuesta.status_code == 422


@pytest.mark.parametrize("descripcion", ["", " ", "\n"])
def test_rechazar_descripcion_de_estimulo_vacia(client, animal_prueba, descripcion):
    respuesta = client.post(
        "/api/actividades/enriquecimientos",
        json=_cuerpo_enriquecimiento(
            animal_prueba["id_animal"],
            descripcion_estimulo=descripcion,
        ),
    )

    assert respuesta.status_code == 422


def test_rechazar_hora_ausente(client, animal_prueba):
    cuerpo = _cuerpo_enriquecimiento(animal_prueba["id_animal"])
    cuerpo.pop("hora_programada")

    assert client.post("/api/actividades/enriquecimientos", json=cuerpo).status_code == 422


def test_rechazar_animal_inexistente(client):
    respuesta = client.post(
        "/api/actividades/enriquecimientos",
        json=_cuerpo_enriquecimiento(999999),
    )

    assert respuesta.status_code == 404


def test_consultar_enriquecimientos_por_rango_de_fechas(client, animal_prueba):
    for fecha in ("2026-05-01", "2026-05-10", "2026-05-20"):
        client.post(
            "/api/actividades/enriquecimientos",
            json=_cuerpo_enriquecimiento(animal_prueba["id_animal"], fecha_programada=fecha),
        )

    respuesta = client.get(
        "/api/actividades/enriquecimientos",
        params={
            "id_animal": animal_prueba["id_animal"],
            "fecha_desde": "2026-05-05",
            "fecha_hasta": "2026-05-15",
        },
    )

    assert respuesta.status_code == 200
    assert [a["fecha_programada"] for a in respuesta.json()] == ["2026-05-10"]
