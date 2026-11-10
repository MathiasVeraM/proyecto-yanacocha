"""Asume GET /api/actividades y GET /api/actividades/calendario de solo visualización."""

import pytest


def _crear(client, tipo, fecha, **extra):
    datos = {
        "tipo_actividad": tipo,
        "fecha_programada": fecha,
        "hora_programada": "10:00:00",
        "duracion_horas": 0,
        "duracion_minutos": 30,
        "id_animal": 101,
        **extra,
    }
    if tipo == "limpieza":
        datos.pop("id_animal")
        datos["id_recinto"] = 201
        ruta = "/api/actividades/limpiezas"
    else:
        rutas = {
            "alimentacion": "/api/actividades/alimentaciones",
            "enriquecimiento": "/api/actividades/enriquecimientos",
            "entrenamiento": "/api/actividades/entrenamientos",
        }
        ruta = rutas[tipo]
    return client.post(ruta, json=datos)


@pytest.mark.parametrize(
    "filtro,valor",
    [
        ("id_animal", 101),
        ("id_recinto", 201),
        ("tipo_actividad", "entrenamiento"),
        ("completada", "false"),
        ("fecha_desde", "2026-08-01"),
    ],
)
def test_listar_actividades_filtrando_por_campo(client, filtro, valor):
    if filtro == "id_recinto":
        respuesta = _crear(client, "limpieza", "2026-08-10")
    else:
        respuesta = _crear(
            client,
            "entrenamiento",
            "2026-08-10",
            objetivo_entrenamiento="Objetivo",
            tipo_refuerzo="Refuerzo",
            duracion_minutos=15,
        )
    assert respuesta.status_code == 201

    listado = client.get("/api/actividades", params={filtro: valor})

    assert listado.status_code == 200
    assert listado.json()
    if filtro == "tipo_actividad":
        assert all(item[filtro] == valor for item in listado.json())
    elif filtro == "completada":
        assert all(item[filtro] is (valor == "true") for item in listado.json())


def test_filtrar_actividades_por_rango_de_fechas(client, dieta_con_alimentos):
    id_dieta = dieta_con_alimentos["id_dieta"]
    _crear(client, "alimentacion", "2026-08-01", id_dieta=id_dieta)
    _crear(client, "alimentacion", "2026-08-10", id_dieta=id_dieta)
    _crear(client, "alimentacion", "2026-08-20", id_dieta=id_dieta)

    respuesta = client.get(
        "/api/actividades",
        params={"fecha_desde": "2026-08-05", "fecha_hasta": "2026-08-15"},
    )

    assert respuesta.status_code == 200
    assert [a["fecha_programada"] for a in respuesta.json()] == ["2026-08-10"]


def test_evento_de_calendario_calcula_inicio_fin_y_todo_el_dia(
    client, animal_prueba
):
    respuesta = client.post(
        "/api/actividades/entrenamientos",
        json={
            "tipo_actividad": "entrenamiento",
            "id_animal": animal_prueba["id_animal"],
            "fecha_programada": "2026-08-10",
            "hora_programada": "23:00:00",
            "duracion_horas": 1,
            "duracion_minutos": 30,
            "objetivo_entrenamiento": "Regresar al refugio",
            "tipo_refuerzo": "Refuerzo positivo",
        },
    )
    assert respuesta.status_code == 201

    eventos = client.get(
        "/api/actividades/calendario",
        params={"fecha_desde": "2026-08-10", "fecha_hasta": "2026-08-10"},
    ).json()
    evento = next(e for e in eventos if e["id_actividad"] == respuesta.json()["id_actividad"])

    assert evento["inicio"] == "2026-08-10T23:00:00"
    assert evento["fin"] == "2026-08-11T00:30:00"
    assert evento["tipo"] == "entrenamiento"
    assert evento["completada"] is False
    assert evento["todo_el_dia"] is False


def test_actividad_sin_hora_es_evento_de_dia_completo(client, recinto_prueba):
    respuesta = client.post(
        "/api/actividades/limpiezas",
        json={
            "id_recinto": recinto_prueba["id_recinto"],
            "fecha_programada": "2026-08-11",
            "duracion_horas": 1,
            "duracion_minutos": 0,
        },
    )
    assert respuesta.status_code == 201

    eventos = client.get(
        "/api/actividades/calendario",
        params={"fecha_desde": "2026-08-11", "fecha_hasta": "2026-08-11"},
    ).json()
    evento = next(e for e in eventos if e["id_actividad"] == respuesta.json()["id_actividad"])
    assert evento["todo_el_dia"] is True
    assert evento["inicio"] == "2026-08-11"
    assert evento["fin"] == "2026-08-11"


def test_duracion_cero_es_evento_puntual(client, animal_prueba, dieta_con_alimentos):
    respuesta = client.post(
        "/api/actividades/alimentaciones",
        json={
            "tipo_actividad": "alimentacion",
            "id_animal": animal_prueba["id_animal"],
            "id_dieta": dieta_con_alimentos["id_dieta"],
            "fecha_programada": "2026-08-12",
            "hora_programada": "12:00:00",
            "duracion_horas": 0,
            "duracion_minutos": 0,
        },
    )
    assert respuesta.status_code == 201

    evento = next(
        e
        for e in client.get(
            "/api/actividades/calendario",
            params={"fecha_desde": "2026-08-12", "fecha_hasta": "2026-08-12"},
        ).json()
        if e["id_actividad"] == respuesta.json()["id_actividad"]
    )
    assert evento["inicio"] == evento["fin"] == "2026-08-12T12:00:00"


def test_rango_sin_resultados_devuelve_lista_vacia(client):
    respuesta = client.get(
        "/api/actividades",
        params={"fecha_desde": "2099-01-01", "fecha_hasta": "2099-01-02"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_calendario_incluye_varios_tipos_el_mismo_dia(
    client, animal_prueba, recinto_prueba, dieta_con_alimentos
):
    _crear(
        client,
        "alimentacion",
        "2026-08-15",
        id_dieta=dieta_con_alimentos["id_dieta"],
        hora_programada="08:00:00",
    )
    _crear(
        client,
        "enriquecimiento",
        "2026-08-15",
        tipo_enriquecimiento="cognitivo",
        descripcion_estimulo="Búsqueda de alimento",
        hora_programada="10:00:00",
    )
    _crear(
        client,
        "limpieza",
        "2026-08-15",
        id_recinto=recinto_prueba["id_recinto"],
    )

    eventos = client.get(
        "/api/actividades/calendario",
        params={"fecha_desde": "2026-08-15", "fecha_hasta": "2026-08-15"},
    ).json()

    assert {e["tipo"] for e in eventos} >= {"alimentacion", "enriquecimiento", "limpieza"}
