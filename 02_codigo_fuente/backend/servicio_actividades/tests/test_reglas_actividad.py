"""Reglas de fechas, duración, duplicados, cruces, edición, eliminación, repetición y dietas.

"Ahora" está fijo en el 02/01/2026 08:00 (fixture ahora_fijo de conftest).
"""

from datetime import datetime

import pytest

URL = "/api/actividades"


def _enriquecimiento(animal, **extra):
    return {
        "id_animal": animal["id_animal"],
        "tipo_enriquecimiento": "sensorial",
        "fecha_programada": "2026-01-02",
        "hora_programada": "10:00:00",
        "descripcion_estimulo": "Ramas con hojas",
        **extra,
    }


def _crear_enriquecimiento(client, animal, params=None, **extra):
    return client.post(f"{URL}/enriquecimientos", json=_enriquecimiento(animal, **extra), params=params)


# ---- Límites ----

def test_limites_para_el_frontend(client):
    limites = client.get(f"{URL}/limites").json()
    assert limites["hoy"] == "2026-01-02"
    assert limites["fecha_min"] == "2026-01-02"
    assert limites["fecha_max"] == "2027-01-02"
    assert limites["duracion_max_minutos"] == 240
    assert limites["duracion_enriquecimiento_minutos"] == 30
    assert limites["repeticion_meses_max"] == 3


# ---- Fechas (30, 39, 40) ----

@pytest.mark.parametrize(
    "fecha,hora",
    [("2026-01-01", "10:00:00"), ("2026-01-02", "07:59:00"), ("1990-05-01", "10:00:00")],
)
def test_no_se_programa_en_el_pasado(client, animal_prueba, fecha, hora):
    respuesta = _crear_enriquecimiento(client, animal_prueba, fecha_programada=fecha, hora_programada=hora)
    assert respuesta.status_code == 422
    assert "pasado" in respuesta.json()["detail"]


def test_se_programa_hasta_un_anio(client, animal_prueba):
    assert _crear_enriquecimiento(client, animal_prueba, fecha_programada="2027-01-02").status_code == 201
    respuesta = _crear_enriquecimiento(client, animal_prueba, fecha_programada="2027-01-03")
    assert respuesta.status_code == 422
    assert "365" in respuesta.json()["detail"]


# ---- Duración (27, 37, 41) ----

def test_enriquecimiento_sin_duracion_toma_30_minutos(client, animal_prueba):
    actividad = _crear_enriquecimiento(client, animal_prueba).json()
    assert (actividad["duracion_horas"], actividad["duracion_minutos"]) == (0, 30)


@pytest.mark.parametrize("tipo", ["entrenamiento", "limpieza", "enriquecimiento"])
def test_duracion_maxima_4_horas(crear_actividad, tipo):
    extra = {"objetivo_entrenamiento": "Target", "tipo_refuerzo": "Fruta"} if tipo == "entrenamiento" else {}
    if tipo == "enriquecimiento":
        extra = {"tipo_enriquecimiento": "social", "descripcion_estimulo": "Espejo"}
    assert crear_actividad(tipo, duracion_horas=4, duracion_minutos=0, **extra).status_code == 201
    respuesta = crear_actividad(
        tipo, duracion_horas=4, duracion_minutos=1, hora_programada="15:00:00", **extra
    )
    assert respuesta.status_code == 422
    assert "4 horas" in respuesta.json()["detail"]


# ---- Duplicado exacto (25, 28) ----

def test_duplicado_exacto_responde_409(client, animal_prueba):
    assert _crear_enriquecimiento(client, animal_prueba).status_code == 201
    respuesta = _crear_enriquecimiento(client, animal_prueba, params={"permitir_cruce": "true"})
    assert respuesta.status_code == 409
    assert "Ya existe una actividad igual" in respuesta.json()["detail"]


def test_limpieza_duplicada_en_el_mismo_recinto_409(crear_actividad):
    assert crear_actividad("limpieza").status_code == 201
    assert crear_actividad("limpieza").status_code == 409


def test_alimentacion_manual_no_duplica_una_toma_de_la_misma_dieta(client, animal_prueba, dieta_con_alimentos, ahora_fijo):
    ahora_fijo(datetime(2026, 1, 1, 0, 0))
    tomas = client.post(
        f"{URL}/tomas/generar", json={"id_dieta": dieta_con_alimentos["id_dieta"], "fecha_hasta": "2026-01-02"}
    ).json()["tomas"]
    toma = next(t for t in tomas if t["fecha_programada"] == "2026-01-02")
    respuesta = client.post(
        f"{URL}/alimentaciones",
        json={
            "id_animal": animal_prueba["id_animal"],
            "id_dieta": dieta_con_alimentos["id_dieta"],
            "fecha_programada": toma["fecha_programada"],
            "hora_programada": toma["hora_programada"],
        },
        params={"permitir_cruce": "true"},
    )
    assert respuesta.status_code == 409
    assert "toma de esa dieta" in respuesta.json()["detail"]


# ---- Cruces de horario (26, 42) ----

def test_cruce_de_horario_pide_confirmacion_y_permite_crear_igual(client, animal_prueba):
    assert _crear_enriquecimiento(client, animal_prueba, hora_programada="10:00:00").status_code == 201
    # 10:15 cae dentro de los 30 minutos del enriquecimiento de las 10:00
    respuesta = client.post(
        f"{URL}/entrenamientos",
        json={
            "id_animal": animal_prueba["id_animal"],
            "fecha_programada": "2026-01-02",
            "hora_programada": "10:15:00",
            "duracion_horas": 0,
            "duracion_minutos": 30,
            "objetivo_entrenamiento": "Target",
            "tipo_refuerzo": "Fruta",
        },
    )
    assert respuesta.status_code == 409
    detalle = respuesta.json()["detail"]
    assert detalle["codigo"] == "cruce_horario"
    assert detalle["cruces"][0]["hora_programada"] == "10:00"

    confirmada = client.post(
        f"{URL}/entrenamientos",
        json={
            "id_animal": animal_prueba["id_animal"],
            "fecha_programada": "2026-01-02",
            "hora_programada": "10:15:00",
            "duracion_horas": 0,
            "duracion_minutos": 30,
            "objetivo_entrenamiento": "Target",
            "tipo_refuerzo": "Fruta",
        },
        params={"permitir_cruce": "true"},
    )
    assert confirmada.status_code == 201


def test_actividades_que_no_se_tocan_no_son_cruce(client, animal_prueba):
    assert _crear_enriquecimiento(client, animal_prueba, hora_programada="10:00:00").status_code == 201
    assert _crear_enriquecimiento(
        client, animal_prueba, hora_programada="10:30:00", tipo_enriquecimiento="social"
    ).status_code == 201


# ---- Completar (31) ----

def test_no_se_completa_una_actividad_futura(client, animal_prueba, ahora_fijo):
    actividad = _crear_enriquecimiento(client, animal_prueba, fecha_programada="2026-01-05").json()
    respuesta = client.post(f"{URL}/{actividad['id_actividad']}/completar", json={})
    assert respuesta.status_code == 409
    assert "hoy o de días anteriores" in respuesta.json()["detail"]
    ahora_fijo(datetime(2026, 1, 5, 12, 0))
    assert client.post(f"{URL}/{actividad['id_actividad']}/completar", json={}).status_code == 200


# ---- Editar y eliminar (29) ----

def test_editar_actividad_pendiente(client, animal_prueba):
    actividad = _crear_enriquecimiento(client, animal_prueba).json()
    respuesta = client.put(
        f"{URL}/{actividad['id_actividad']}",
        json={"hora_programada": "11:00:00", "descripcion_estimulo": "Hielo con fruta"},
    )
    assert respuesta.status_code == 200
    editada = respuesta.json()
    assert editada["hora_programada"] == "11:00:00"
    assert editada["descripcion_estimulo"] == "Hielo con fruta"


def test_editar_respeta_las_reglas(client, animal_prueba):
    actividad = _crear_enriquecimiento(client, animal_prueba).json()
    url = f"{URL}/{actividad['id_actividad']}"
    assert client.put(url, json={"fecha_programada": "2025-12-31"}).status_code == 422
    assert client.put(url, json={"duracion_horas": 5}).status_code == 422
    # Cambiar solo las observaciones no se considera "programar"
    assert client.put(url, json={"observaciones": "Traer guantes"}).status_code == 200


def test_editar_o_eliminar_una_completada_responde_409(client, animal_prueba, ahora_fijo):
    actividad = _crear_enriquecimiento(client, animal_prueba).json()
    ahora_fijo(datetime(2026, 1, 2, 12, 0))
    client.post(f"{URL}/{actividad['id_actividad']}/completar", json={})
    assert client.put(f"{URL}/{actividad['id_actividad']}", json={"observaciones": "x"}).status_code == 409
    assert client.delete(f"{URL}/{actividad['id_actividad']}").status_code == 409


def test_eliminar_actividad_pendiente_con_sus_observaciones(client, animal_prueba):
    actividad = _crear_enriquecimiento(client, animal_prueba).json()
    client.post(
        f"{URL}/{actividad['id_actividad']}/observaciones",
        json={"categoria": "comportamiento", "severidad": "bajo", "detalle": "Se mostró tranquilo"},
    )
    assert client.delete(f"{URL}/{actividad['id_actividad']}").status_code == 204
    assert client.get(f"{URL}/{actividad['id_actividad']}").status_code == 404


# ---- Repetición (42) ----

def _repetida(animal, repeticion, **extra):
    return {
        "tipo_actividad": "enriquecimiento",
        "id_animal": animal["id_animal"],
        "tipo_enriquecimiento": "cognitivo",
        "descripcion_estimulo": "Rompecabezas",
        "fecha_programada": "2026-01-05",
        "hora_programada": "08:00:00",
        "repeticion": repeticion,
        **extra,
    }


def test_repetir_todos_los_dias_hasta_una_fecha(client, animal_prueba):
    respuesta = client.post(f"{URL}/repetidas", json=_repetida(animal_prueba, {"fecha_fin": "2026-01-11"}))
    assert respuesta.status_code == 201
    assert [a["fecha_programada"] for a in respuesta.json()] == [
        f"2026-01-{dia:02d}" for dia in range(5, 12)
    ]


def test_repetir_ciertos_dias_durante_un_mes(client, animal_prueba):
    # Lunes, miércoles y viernes desde el lunes 05/01 durante 1 mes (hasta el 04/02)
    respuesta = client.post(
        f"{URL}/repetidas", json=_repetida(animal_prueba, {"dias_semana": [0, 2, 4], "meses": 1})
    )
    assert respuesta.status_code == 201
    fechas = [datetime.fromisoformat(a["fecha_programada"]) for a in respuesta.json()]
    assert {f.weekday() for f in fechas} == {0, 2, 4}
    assert fechas[0].date().isoformat() == "2026-01-05"
    assert fechas[-1].date().isoformat() == "2026-02-04"


def test_repeticion_maximo_tres_meses(client, animal_prueba):
    assert client.post(f"{URL}/repetidas", json=_repetida(animal_prueba, {"meses": 4})).status_code == 422
    respuesta = client.post(f"{URL}/repetidas", json=_repetida(animal_prueba, {"fecha_fin": "2026-04-10"}))
    assert respuesta.status_code == 422


def test_repeticion_con_cruce_pregunta_y_luego_crea_todo(client, animal_prueba):
    _crear_enriquecimiento(client, animal_prueba, fecha_programada="2026-01-07", hora_programada="08:10:00")
    cuerpo = _repetida(animal_prueba, {"fecha_fin": "2026-01-09"})
    respuesta = client.post(f"{URL}/repetidas", json=cuerpo)
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["codigo"] == "cruce_horario"
    confirmada = client.post(f"{URL}/repetidas", json=cuerpo, params={"permitir_cruce": "true"})
    assert confirmada.status_code == 201
    assert len(confirmada.json()) == 5


def test_repeticion_con_duplicado_no_crea_nada(client, animal_prueba):
    _crear_enriquecimiento(
        client, animal_prueba, fecha_programada="2026-01-06", hora_programada="08:00:00",
        tipo_enriquecimiento="cognitivo",
    )
    respuesta = client.post(
        f"{URL}/repetidas",
        json=_repetida(animal_prueba, {"fecha_fin": "2026-01-08"}),
        params={"permitir_cruce": "true"},
    )
    assert respuesta.status_code == 409
    assert "06/01" in respuesta.json()["detail"]
    assert len(client.get(URL, params={"tipo_actividad": "enriquecimiento"}).json()) == 1


# ---- Dietas (32, 33) ----

def _dieta(animal, **extra):
    return {
        "id_animal": animal["id_animal"],
        "fecha_inicio": "2026-01-02",
        "frecuencia_valor": 1,
        "frecuencia_unidad": "dias",
        "alimentos": [{"nombre_alimento": "Fruta", "cantidad_gramos": 100}],
        **extra,
    }


def test_dieta_nueva_no_empieza_antes_de_la_vigente(client, animal_prueba, dieta_con_alimentos):
    # La vigente empieza el 01/01
    respuesta = client.post(f"{URL}/dietas", json=_dieta(animal_prueba, fecha_inicio="2026-01-01"))
    assert respuesta.status_code == 422
    assert "dieta vigente" in respuesta.json()["detail"]


def test_dieta_empieza_como_maximo_30_dias_despues(client, animal_prueba):
    assert client.post(f"{URL}/dietas", json=_dieta(animal_prueba, fecha_inicio="2026-02-02")).status_code == 422
    assert client.post(f"{URL}/dietas", json=_dieta(animal_prueba, fecha_inicio="2026-02-01")).status_code == 201


def test_finalizar_dieta_guarda_la_fecha_de_hoy(client, dieta_con_alimentos):
    respuesta = client.post(f"{URL}/dietas/{dieta_con_alimentos['id_dieta']}/finalizar")
    assert respuesta.status_code == 200
    dieta = respuesta.json()
    assert dieta["fecha_fin"] == "2026-01-02"
    assert dieta["vigente"] is False
    # Ya no está vigente: no se puede volver a finalizar
    assert client.post(f"{URL}/dietas/{dieta_con_alimentos['id_dieta']}/finalizar").status_code == 409


def test_cambiar_fin_de_la_dieta(client, dieta_con_alimentos):
    url = f"{URL}/dietas/{dieta_con_alimentos['id_dieta']}"
    assert client.patch(url, json={"fecha_fin": "2025-12-31"}).status_code == 422
    respuesta = client.patch(url, json={"fecha_fin": "2026-03-01"})
    assert respuesta.status_code == 200
    assert respuesta.json()["fecha_fin"] == "2026-03-01"
    assert client.patch(url, json={"fecha_fin": None}).json()["fecha_fin"] is None
