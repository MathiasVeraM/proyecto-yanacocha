"""Asume POST /api/actividades/tomas/generar y asociación con actividad_alimentacion."""

import pytest


@pytest.mark.parametrize(
    "valor,unidad,desde,hasta,cantidad_esperada",
    [
        (1, "dias", "2026-03-01", "2026-03-03", 3),
        (12, "horas", "2026-03-01", "2026-03-02", 4),
        (2, "dias", "2026-03-01", "2026-03-05", 3),
        (1, "semanas", "2026-03-01", "2026-03-15", 3),
    ],
)
def test_generar_tomas_segun_frecuencia(
    client,
    animal_prueba,
    valor,
    unidad,
    desde,
    hasta,
    cantidad_esperada,
):
    dieta = client.post(
        "/api/actividades/dietas",
        json={
            "id_animal": animal_prueba["id_animal"],
            "fecha_inicio": desde,
            "frecuencia_valor": valor,
            "frecuencia_unidad": unidad,
            "alimentos": [{"nombre_alimento": "Fruta", "cantidad_gramos": 100}],
        },
    ).json()

    respuesta = client.post(
        "/api/actividades/tomas/generar",
        json={"id_dieta": dieta["id_dieta"], "fecha_hasta": hasta},
    )

    assert respuesta.status_code == 200
    tomas = respuesta.json()["tomas"]
    assert len(tomas) == cantidad_esperada
    assert all(t["tipo_actividad"] == "alimentacion" for t in tomas)
    assert all(t["completada"] is False for t in tomas)
    assert all(t["id_dieta"] == dieta["id_dieta"] for t in tomas)


def test_generar_tomas_respeta_horizonte_y_fecha_fin(
    client, animal_prueba
):
    dieta = client.post(
        "/api/actividades/dietas",
        json={
            "id_animal": animal_prueba["id_animal"],
            "fecha_inicio": "2026-04-01",
            "fecha_fin": "2026-04-03",
            "frecuencia_valor": 1,
            "frecuencia_unidad": "dias",
            "alimentos": [{"nombre_alimento": "Fruta", "cantidad_gramos": 100}],
        },
    ).json()

    respuesta = client.post(
        "/api/actividades/tomas/generar",
        json={"id_dieta": dieta["id_dieta"], "fecha_hasta": "2026-04-10"},
    )

    assert respuesta.status_code == 200
    assert [t["fecha_programada"] for t in respuesta.json()["tomas"]] == [
        "2026-04-01",
        "2026-04-02",
        "2026-04-03",
    ]


def test_regenerar_tomas_es_idempotente(client, dieta_con_alimentos):
    cuerpo = {"id_dieta": dieta_con_alimentos["id_dieta"], "fecha_hasta": "2026-01-03"}

    primera = client.post("/api/actividades/tomas/generar", json=cuerpo)
    segunda = client.post("/api/actividades/tomas/generar", json=cuerpo)

    assert primera.status_code == segunda.status_code == 200
    ids_primera = {t["id_actividad"] for t in primera.json()["tomas"]}
    ids_segunda = {t["id_actividad"] for t in segunda.json()["tomas"]}
    assert ids_primera == ids_segunda
    assert len(client.get("/api/actividades", params={"tipo_actividad": "alimentacion"}).json()) == len(
        ids_primera
    )


def test_reemplazar_dieta_cancela_solo_tomas_futuras_pendientes(
    client, dieta_con_alimentos, animal_prueba
):
    generadas = client.post(
        "/api/actividades/tomas/generar",
        json={"id_dieta": dieta_con_alimentos["id_dieta"], "fecha_hasta": "2026-01-04"},
    ).json()["tomas"]
    completada = client.post(
        f"/api/actividades/{generadas[0]['id_actividad']}/completar",
        json={"observaciones": "Toma realizada"},
    ).json()

    client.post(
        "/api/actividades/dietas",
        json={
            "id_animal": animal_prueba["id_animal"],
            "fecha_inicio": "2026-01-02",
            "frecuencia_valor": 1,
            "frecuencia_unidad": "dias",
            "alimentos": [{"nombre_alimento": "Hojas", "cantidad_gramos": 80}],
        },
    )
    restantes = client.get("/api/actividades", params={"tipo_actividad": "alimentacion"}).json()

    toma_completada = next(t for t in restantes if t["id_actividad"] == completada["id_actividad"])
    assert toma_completada["completada"] is True
    assert all(
        t["cancelada"] or t["completada"]
        for t in restantes
        if t["id_dieta"] == dieta_con_alimentos["id_dieta"]
    )
