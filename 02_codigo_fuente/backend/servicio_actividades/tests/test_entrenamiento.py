"""Asume POST /api/actividades/entrenamientos."""

import pytest


def _cuerpo_entrenamiento(animal_id, **extra):
    return {
        "id_animal": animal_id,
        "fecha_programada": "2026-06-01",
        "hora_programada": "11:00:00",
        "objetivo_entrenamiento": "Acudir a la estación de manejo",
        "tipo_refuerzo": "Refuerzo positivo",
        "duracion_horas": 1,
        "duracion_minutos": 15,
        **extra,
    }


def test_programar_entrenamiento_y_devolver_duracion(client, animal_prueba):
    respuesta = client.post(
        "/api/actividades/entrenamientos",
        json=_cuerpo_entrenamiento(animal_prueba["id_animal"]),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["duracion_horas"] == 1
    assert respuesta.json()["duracion_minutos"] == 15
    assert respuesta.json()["objetivo_entrenamiento"] == "Acudir a la estación de manejo"


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("objetivo_entrenamiento", ""),
        ("objetivo_entrenamiento", " "),
        ("tipo_refuerzo", ""),
        ("tipo_refuerzo", " "),
    ],
)
def test_rechazar_objetivo_o_refuerzo_vacio(client, animal_prueba, campo, valor):
    respuesta = client.post(
        "/api/actividades/entrenamientos",
        json=_cuerpo_entrenamiento(animal_prueba["id_animal"], **{campo: valor}),
    )

    assert respuesta.status_code == 422


def test_rechazar_duracion_total_cero(client, animal_prueba):
    respuesta = client.post(
        "/api/actividades/entrenamientos",
        json=_cuerpo_entrenamiento(
            animal_prueba["id_animal"],
            duracion_horas=0,
            duracion_minutos=0,
        ),
    )

    assert respuesta.status_code == 422


@pytest.mark.parametrize("minutos", [-1, 60, 120])
def test_rechazar_minutos_fuera_de_rango(client, animal_prueba, minutos):
    respuesta = client.post(
        "/api/actividades/entrenamientos",
        json=_cuerpo_entrenamiento(animal_prueba["id_animal"], duracion_minutos=minutos),
    )

    assert respuesta.status_code == 422


def test_rechazar_horas_negativas(client, animal_prueba):
    respuesta = client.post(
        "/api/actividades/entrenamientos",
        json=_cuerpo_entrenamiento(animal_prueba["id_animal"], duracion_horas=-1),
    )

    assert respuesta.status_code == 422


def test_rechazar_hora_ausente(client, animal_prueba):
    cuerpo = _cuerpo_entrenamiento(animal_prueba["id_animal"])
    cuerpo.pop("hora_programada")

    assert client.post("/api/actividades/entrenamientos", json=cuerpo).status_code == 422


def test_rechazar_animal_inexistente(client):
    respuesta = client.post(
        "/api/actividades/entrenamientos",
        json=_cuerpo_entrenamiento(999999),
    )

    assert respuesta.status_code == 404
