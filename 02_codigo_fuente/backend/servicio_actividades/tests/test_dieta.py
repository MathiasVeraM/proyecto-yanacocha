"""Asume POST/GET /api/actividades/dietas y GET /api/actividades/animales/{id}/dietas."""

import pytest


def _nueva_dieta(animal_id, **extra):
    return {
        "id_animal": animal_id,
        "fecha_inicio": "2026-02-01",
        "frecuencia_valor": 1,
        "frecuencia_unidad": "dias",
        "alimentos": [{"nombre_alimento": "Fruta", "cantidad_gramos": 120}],
        **extra,
    }


def test_asignar_dieta_guarda_alimentos_y_usuario_creador(client, animal_prueba, usuario_prueba):
    respuesta = client.post("/api/actividades/dietas", json=_nueva_dieta(animal_prueba["id_animal"]))

    assert respuesta.status_code == 201
    dieta = respuesta.json()
    assert dieta["id_animal"] == animal_prueba["id_animal"]
    assert dieta["id_usuario_creador"] == usuario_prueba["id_usuario"]
    assert dieta["alimentos"][0]["nombre_alimento"] == "Fruta"
    assert dieta["alimentos"][0]["cantidad_gramos"] == 120


def test_consultar_historial_y_dieta_vigente(client, dieta_con_alimentos, animal_prueba):
    respuesta = client.get(f"/api/actividades/animales/{animal_prueba['id_animal']}/dietas")

    assert respuesta.status_code == 200
    historial = respuesta.json()
    assert [d["id_dieta"] for d in historial] == [dieta_con_alimentos["id_dieta"]]
    assert historial[0]["vigente"] is True
    assert client.get(
        f"/api/actividades/animales/{animal_prueba['id_animal']}/dietas/vigente"
    ).json()["id_dieta"] == dieta_con_alimentos["id_dieta"]


def test_reemplazar_dieta_cierra_la_anterior_en_la_misma_operacion(
    client, dieta_con_alimentos, animal_prueba
):
    respuesta = client.post(
        "/api/actividades/dietas",
        json=_nueva_dieta(
            animal_prueba["id_animal"],
            fecha_inicio="2026-02-10",
            alimentos=[{"nombre_alimento": "Hojas", "cantidad_gramos": 200}],
        ),
    )

    assert respuesta.status_code == 201
    historial = client.get(
        f"/api/actividades/animales/{animal_prueba['id_animal']}/dietas"
    ).json()
    assert len([d for d in historial if d["vigente"]]) == 1
    anterior = next(d for d in historial if d["id_dieta"] == dieta_con_alimentos["id_dieta"])
    assert anterior["vigente"] is False
    assert anterior["fecha_fin"] == "2026-02-09"
    assert historial[0]["id_dieta"] == respuesta.json()["id_dieta"]


@pytest.mark.parametrize("unidad", ["horas", "dias", "semanas"])
def test_asignar_dieta_acepta_unidades_configurables(client, animal_prueba, unidad):
    respuesta = client.post(
        "/api/actividades/dietas",
        json=_nueva_dieta(animal_prueba["id_animal"], frecuencia_unidad=unidad),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["frecuencia_unidad"] == unidad


@pytest.mark.parametrize(
    "cambios",
    [
        {"frecuencia_unidad": "meses"},
        {"frecuencia_valor": 0},
        {"frecuencia_valor": -1},
    ],
)
def test_asignar_dieta_rechaza_frecuencia_invalida(client, animal_prueba, cambios):
    respuesta = client.post(
        "/api/actividades/dietas",
        json=_nueva_dieta(animal_prueba["id_animal"], **cambios),
    )

    assert respuesta.status_code == 422


def test_asignar_dieta_rechaza_animal_inexistente(client):
    respuesta = client.post("/api/actividades/dietas", json=_nueva_dieta(999999))

    assert respuesta.status_code == 404


def test_asignar_dieta_rechaza_lista_de_alimentos_vacia(client, animal_prueba):
    respuesta = client.post(
        "/api/actividades/dietas",
        json=_nueva_dieta(animal_prueba["id_animal"], alimentos=[]),
    )

    assert respuesta.status_code == 422


@pytest.mark.parametrize("cantidad", [0, -0.01])
def test_asignar_dieta_rechaza_cantidad_no_positiva(client, animal_prueba, cantidad):
    respuesta = client.post(
        "/api/actividades/dietas",
        json=_nueva_dieta(
            animal_prueba["id_animal"],
            alimentos=[{"nombre_alimento": "Fruta", "cantidad_gramos": cantidad}],
        ),
    )

    assert respuesta.status_code == 422


def test_asignar_dieta_rechaza_nombre_de_alimento_vacio(client, animal_prueba):
    respuesta = client.post(
        "/api/actividades/dietas",
        json=_nueva_dieta(
            animal_prueba["id_animal"],
            alimentos=[{"nombre_alimento": " ", "cantidad_gramos": 10}],
        ),
    )

    assert respuesta.status_code == 422


def test_asignar_dieta_rechaza_fecha_fin_anterior_a_inicio(client, animal_prueba):
    respuesta = client.post(
        "/api/actividades/dietas",
        json=_nueva_dieta(
            animal_prueba["id_animal"],
            fecha_inicio="2026-02-10",
            fecha_fin="2026-02-09",
        ),
    )

    assert respuesta.status_code == 422


def test_historial_ordena_dietas_de_la_mas_reciente_a_la_mas_antigua(
    client, animal_prueba, dieta_con_alimentos
):
    nueva = client.post(
        "/api/actividades/dietas",
        json=_nueva_dieta(
            animal_prueba["id_animal"],
            fecha_inicio="2026-02-01",
            alimentos=[{"nombre_alimento": "Hojas", "cantidad_gramos": 90}],
        ),
    ).json()

    historial = client.get(
        f"/api/actividades/animales/{animal_prueba['id_animal']}/dietas"
    ).json()

    assert [d["id_dieta"] for d in historial] == [
        nueva["id_dieta"],
        dieta_con_alimentos["id_dieta"],
    ]
