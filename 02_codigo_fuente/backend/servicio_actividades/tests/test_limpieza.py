"""Asume POST /api/actividades/limpiezas; las limpiezas usan actividad sin animal."""

import pytest


def _cuerpo_limpieza(recinto_id, **extra):
    return {
        "id_recinto": recinto_id,
        "fecha_programada": "2026-07-01",
        "duracion_horas": 1,
        "duracion_minutos": 0,
        **extra,
    }


def test_programar_limpieza_asociada_solo_a_recinto(client, recinto_prueba):
    respuesta = client.post(
        "/api/actividades/limpiezas",
        json=_cuerpo_limpieza(recinto_prueba["id_recinto"]),
    )

    assert respuesta.status_code == 201
    limpieza = respuesta.json()
    assert limpieza["tipo_actividad"] == "limpieza"
    assert limpieza["id_recinto"] == recinto_prueba["id_recinto"]
    assert limpieza["id_animal"] is None


def test_ignorar_id_animal_en_limpieza_sin_asociarlo(client, recinto_prueba, animal_prueba):
    respuesta = client.post(
        "/api/actividades/limpiezas",
        json=_cuerpo_limpieza(
            recinto_prueba["id_recinto"],
            id_animal=animal_prueba["id_animal"],
        ),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["id_animal"] is None


def test_rechazar_recinto_inexistente(client):
    respuesta = client.post("/api/actividades/limpiezas", json=_cuerpo_limpieza(999999))

    assert respuesta.status_code == 404


def test_rechazar_duracion_total_cero(client, recinto_prueba):
    respuesta = client.post(
        "/api/actividades/limpiezas",
        json=_cuerpo_limpieza(
            recinto_prueba["id_recinto"],
            duracion_horas=0,
            duracion_minutos=0,
        ),
    )

    assert respuesta.status_code == 422


@pytest.mark.parametrize("minutos", [-1, 60])
def test_rechazar_minutos_fuera_de_rango(client, recinto_prueba, minutos):
    respuesta = client.post(
        "/api/actividades/limpiezas",
        json=_cuerpo_limpieza(
            recinto_prueba["id_recinto"],
            duracion_minutos=minutos,
        ),
    )

    assert respuesta.status_code == 422
