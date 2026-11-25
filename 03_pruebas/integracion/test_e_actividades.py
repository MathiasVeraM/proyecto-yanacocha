"""e) Actividades: crear, listar, calendario, completar, reabrir, duplicados, cruces y observaciones.

Las fechas se calculan en hora de Ecuador y nunca están en el pasado. Para poder completar una actividad
(solo se permite hoy o antes) se usa una limpieza de hoy sin hora, que el sistema acepta.
"""
from datetime import date, timedelta

import pytest

from ayudas import (
    ahora_ec,
    datos_enriquecimiento,
    datos_entrenamiento,
    datos_limpieza,
    en_dias,
    exigir,
    hoy_ec,
    iso,
)


@pytest.fixture
def limpieza_de_hoy(programar, recinto):
    return exigir(programar(datos_limpieza(recinto["id_recinto"], hoy_ec())), 201)


# ---------- Crear ----------

def test_los_limites_usan_la_fecha_de_ecuador(api_manejo):
    limites = exigir(api_manejo.get("/api/actividades/limites"))

    # Si la prueba cruza la medianoche de Ecuador, la fecha puede cambiar entre las dos lecturas
    assert limites["hoy"] in (iso(hoy_ec()), iso(hoy_ec() - timedelta(days=1)))
    assert limites["fecha_min"] == limites["hoy"]


def test_crear_enriquecimiento_usa_la_duracion_por_defecto(programar, animal, usuarios):
    actividad = exigir(programar(datos_enriquecimiento(animal["id_animal"], en_dias(2))), 201)

    assert actividad["tipo_actividad"] == "enriquecimiento"
    assert actividad["id_animal"] == animal["id_animal"]
    assert actividad["fecha_programada"] == iso(en_dias(2))
    assert actividad["hora_programada"] == "10:00:00"
    assert (actividad["duracion_horas"], actividad["duracion_minutos"]) == (0, 30)
    assert actividad["completada"] is False
    assert actividad["id_usuario_programo"] == usuarios["manejo"].id_usuario


def test_crear_entrenamiento(programar, animal):
    actividad = exigir(programar(datos_entrenamiento(animal["id_animal"], en_dias(2))), 201)

    assert actividad["tipo_actividad"] == "entrenamiento"
    assert actividad["objetivo_entrenamiento"] == "Entrar al transportador"
    assert (actividad["duracion_horas"], actividad["duracion_minutos"]) == (1, 0)


def test_crear_limpieza_de_un_recinto(programar, recinto):
    actividad = exigir(programar(datos_limpieza(recinto["id_recinto"], en_dias(2), "08:00")), 201)

    assert actividad["id_recinto"] == recinto["id_recinto"]
    assert actividad["id_animal"] is None


@pytest.mark.parametrize(
    "cambios",
    [
        {"objetivo_entrenamiento": None},
        {"tipo_refuerzo": None},
        {"duracion_horas": 0, "duracion_minutos": 0},
        {"hora_programada": None},
    ],
)
def test_entrenamiento_incompleto_422(programar, animal, cambios):
    datos = {**datos_entrenamiento(animal["id_animal"], en_dias(2)), **cambios}

    assert programar(datos).status_code == 422


def test_limpieza_sin_duracion_o_con_animal_422(programar, animal, recinto):
    sin_duracion = datos_limpieza(recinto["id_recinto"], en_dias(2), "08:00", minutos=0)
    con_animal = {**datos_limpieza(recinto["id_recinto"], en_dias(2), "09:00"), "id_animal": animal["id_animal"]}

    assert programar(sin_duracion).status_code == 422
    assert programar(con_animal).status_code == 422


def test_actividad_de_un_animal_o_recinto_inexistente_404(programar):
    assert programar(datos_enriquecimiento(2147483647, en_dias(2))).status_code == 404
    assert programar(datos_limpieza(2147483647, en_dias(2), "08:00")).status_code == 404


def test_no_se_programa_en_el_pasado(programar, animal):
    assert programar(datos_enriquecimiento(animal["id_animal"], en_dias(-1))).status_code == 422


def test_no_se_programa_una_hora_que_ya_paso_hoy(programar, animal):
    ahora = ahora_ec()
    if ahora.hour < 1:
        pytest.skip("Pasada la medianoche no hay una hora anterior dentro del mismo día")
    hora_pasada = (ahora - timedelta(hours=1)).strftime("%H:%M")

    assert programar(datos_enriquecimiento(animal["id_animal"], hoy_ec(), hora_pasada)).status_code == 422


def test_no_se_programa_mas_alla_del_limite(programar, animal, api_manejo):
    maximo = exigir(api_manejo.get("/api/actividades/limites"))["fecha_max"]
    despues = date.fromisoformat(maximo) + timedelta(days=1)

    assert programar(datos_enriquecimiento(animal["id_animal"], despues)).status_code == 422


def test_duracion_maxima(programar, animal):
    datos = {**datos_entrenamiento(animal["id_animal"], en_dias(2)), "duracion_horas": 5, "duracion_minutos": 0}

    assert programar(datos).status_code == 422


# ---------- Duplicados y cruces de horario ----------

def test_un_duplicado_exacto_409(programar, animal):
    datos = datos_enriquecimiento(animal["id_animal"], en_dias(3))
    exigir(programar(datos), 201)

    segunda = programar(datos)

    assert segunda.status_code == 409
    assert "igual" in str(segunda.json()["detail"])


def test_un_cruce_de_horario_409_con_la_lista_de_cruces(programar, animal):
    primera = exigir(programar(datos_entrenamiento(animal["id_animal"], en_dias(3), "11:00", 60)), 201)

    cruce = programar(datos_enriquecimiento(animal["id_animal"], en_dias(3), "11:30"))

    assert cruce.status_code == 409
    detalle = cruce.json()["detail"]
    assert detalle["codigo"] == "cruce_horario"
    assert [c["id_actividad"] for c in detalle["cruces"]] == [primera["id_actividad"]]


def test_un_cruce_se_puede_confirmar_con_permitir_cruce(programar, animal):
    exigir(programar(datos_entrenamiento(animal["id_animal"], en_dias(3), "11:00", 60)), 201)

    confirmada = programar(datos_enriquecimiento(animal["id_animal"], en_dias(3), "11:30"), permitir_cruce="true")

    assert confirmada.status_code == 201


def test_actividades_seguidas_sin_solaparse_no_son_un_cruce(programar, animal):
    exigir(programar(datos_entrenamiento(animal["id_animal"], en_dias(3), "11:00", 60)), 201)

    assert programar(datos_enriquecimiento(animal["id_animal"], en_dias(3), "12:00")).status_code == 201


def test_dos_limpiezas_que_se_cruzan_en_el_mismo_recinto_409(programar, recinto):
    exigir(programar(datos_limpieza(recinto["id_recinto"], en_dias(3), "09:00", 60)), 201)

    assert programar(datos_limpieza(recinto["id_recinto"], en_dias(3), "09:30", 30)).status_code == 409


# ---------- Consultar ----------

def test_obtener_actividad_por_id_y_404(api_manejo, programar, animal):
    creada = exigir(programar(datos_enriquecimiento(animal["id_animal"], en_dias(2))), 201)

    obtenida = exigir(api_manejo.get(f"/api/actividades/{creada['id_actividad']}"))

    assert obtenida == creada
    assert api_manejo.get("/api/actividades/2147483647").status_code == 404


def test_listar_con_filtros(api_voluntario, programar, animal):
    id_animal = animal["id_animal"]
    enriquecimiento = exigir(programar(datos_enriquecimiento(id_animal, en_dias(2))), 201)
    entrenamiento = exigir(programar(datos_entrenamiento(id_animal, en_dias(4))), 201)

    todas = exigir(api_voluntario.get("/api/actividades", params={"id_animal": id_animal}))
    solo_entrenamientos = exigir(
        api_voluntario.get("/api/actividades", params={"id_animal": id_animal, "tipo_actividad": "entrenamiento"})
    )
    por_fechas = exigir(
        api_voluntario.get(
            "/api/actividades",
            params={"id_animal": id_animal, "fecha_desde": iso(en_dias(1)), "fecha_hasta": iso(en_dias(3))},
        )
    )
    completadas = exigir(api_voluntario.get("/api/actividades", params={"id_animal": id_animal, "completada": "true"}))

    # Ordenadas por fecha
    assert [a["id_actividad"] for a in todas] == [enriquecimiento["id_actividad"], entrenamiento["id_actividad"]]
    assert [a["id_actividad"] for a in solo_entrenamientos] == [entrenamiento["id_actividad"]]
    assert [a["id_actividad"] for a in por_fechas] == [enriquecimiento["id_actividad"]]
    assert completadas == []


def test_filtro_de_fechas_invertido_422(api_manejo):
    respuesta = api_manejo.get("/api/actividades", params={"fecha_desde": iso(en_dias(5)), "fecha_hasta": iso(en_dias(1))})

    assert respuesta.status_code == 422


def test_calendario_con_horas_y_actividades_de_todo_el_dia(api_voluntario, programar, animal, recinto):
    entrenamiento = exigir(programar(datos_entrenamiento(animal["id_animal"], en_dias(2), "10:00", 90)), 201)
    limpieza = exigir(programar(datos_limpieza(recinto["id_recinto"], en_dias(2))), 201)

    entrenamientos = exigir(api_voluntario.get("/api/actividades/calendario", params={"id_animal": animal["id_animal"]}))
    limpiezas = exigir(api_voluntario.get("/api/actividades/calendario", params={"id_recinto": recinto["id_recinto"]}))

    assert entrenamientos == [
        {
            "id_actividad": entrenamiento["id_actividad"],
            "inicio": f"{iso(en_dias(2))}T10:00:00",
            "fin": f"{iso(en_dias(2))}T11:30:00",
            "tipo": "entrenamiento",
            "completada": False,
            "todo_el_dia": False,
        }
    ]
    assert [(e["id_actividad"], e["tipo"], e["todo_el_dia"]) for e in limpiezas] == [
        (limpieza["id_actividad"], "limpieza", True)
    ]


# ---------- Completar y reabrir ----------

def test_completar_y_reabrir(api_voluntario, api_manejo, limpieza_de_hoy):
    ruta = f"/api/actividades/{limpieza_de_hoy['id_actividad']}"

    completada = exigir(api_voluntario.post(f"{ruta}/completar", json={"observaciones": "Recinto limpio"}))
    assert completada["completada"] is True
    assert completada["observaciones"] == "Recinto limpio"
    assert exigir(api_voluntario.get("/api/actividades", params={"id_recinto": limpieza_de_hoy["id_recinto"], "completada": "true"}))

    reabierta = exigir(api_manejo.post(f"{ruta}/reabrir"))
    assert reabierta["completada"] is False
    assert reabierta["id_usuario_completo"] is None
    assert reabierta["fecha_completada"] is None


def test_completar_dos_veces_409(api_voluntario, limpieza_de_hoy):
    ruta = f"/api/actividades/{limpieza_de_hoy['id_actividad']}/completar"
    exigir(api_voluntario.post(ruta, json={}))

    assert api_voluntario.post(ruta, json={}).status_code == 409


def test_reabrir_una_pendiente_409(api_manejo, limpieza_de_hoy):
    assert api_manejo.post(f"/api/actividades/{limpieza_de_hoy['id_actividad']}/reabrir").status_code == 409


def test_no_se_completa_una_actividad_futura_409(api_voluntario, programar, animal):
    futura = exigir(programar(datos_enriquecimiento(animal["id_animal"], en_dias(2))), 201)

    assert api_voluntario.post(f"/api/actividades/{futura['id_actividad']}/completar", json={}).status_code == 409


def test_completar_una_actividad_inexistente_404(api_voluntario):
    assert api_voluntario.post("/api/actividades/2147483647/completar", json={}).status_code == 404


def test_tras_reabrir_se_puede_completar_de_nuevo(api_voluntario, api_manejo, limpieza_de_hoy):
    ruta = f"/api/actividades/{limpieza_de_hoy['id_actividad']}"
    exigir(api_voluntario.post(f"{ruta}/completar", json={}))
    exigir(api_manejo.post(f"{ruta}/reabrir"))

    assert exigir(api_voluntario.post(f"{ruta}/completar", json={}))["completada"] is True


# ---------- Editar, eliminar y repetir ----------

def test_editar_una_actividad_pendiente(api_manejo, programar, animal):
    creada = exigir(programar(datos_enriquecimiento(animal["id_animal"], en_dias(2))), 201)

    editada = exigir(
        api_manejo.put(f"/api/actividades/{creada['id_actividad']}", json={"hora_programada": "15:00", "observaciones": "Cambio de hora"})
    )

    assert editada["hora_programada"] == "15:00:00"
    assert editada["observaciones"] == "Cambio de hora"


def test_no_se_edita_una_actividad_completada_409(api_manejo, api_voluntario, limpieza_de_hoy):
    ruta = f"/api/actividades/{limpieza_de_hoy['id_actividad']}"
    exigir(api_voluntario.post(f"{ruta}/completar", json={}))

    assert api_manejo.put(ruta, json={"observaciones": "tarde"}).status_code == 409


def test_eliminar_una_actividad(api_manejo, programar, animal):
    creada = exigir(programar(datos_enriquecimiento(animal["id_animal"], en_dias(2))), 201)
    ruta = f"/api/actividades/{creada['id_actividad']}"

    assert api_manejo.delete(ruta).status_code == 204
    assert api_manejo.get(ruta).status_code == 404


@pytest.mark.lento
def test_actividad_repetida_crea_una_por_dia(api_manejo, animal):
    datos = {
        **datos_enriquecimiento(animal["id_animal"], en_dias(2)),
        "repeticion": {"fecha_fin": iso(en_dias(4))},
    }

    creadas = exigir(api_manejo.post("/api/actividades/repetidas", json=datos), 201)
    try:
        assert [a["fecha_programada"] for a in creadas] == [iso(en_dias(2)), iso(en_dias(3)), iso(en_dias(4))]
        # Repetir lo mismo otra vez choca con las ya creadas
        assert api_manejo.post("/api/actividades/repetidas", json=datos).status_code == 409
    finally:
        for actividad in creadas:
            api_manejo.delete(f"/api/actividades/{actividad['id_actividad']}")


def test_repeticion_con_fin_y_meses_a_la_vez_422(api_manejo, animal):
    datos = {
        **datos_enriquecimiento(animal["id_animal"], en_dias(2)),
        "repeticion": {"fecha_fin": iso(en_dias(4)), "meses": 1},
    }

    assert api_manejo.post("/api/actividades/repetidas", json=datos).status_code == 422


# ---------- Observaciones ----------

def _observacion(**cambios):
    return {"categoria": "comportamiento", "severidad": "alto", "detalle": "El ejemplar rechazó el alimento", **cambios}


def test_voluntario_registra_una_observacion_con_alerta(api_voluntario, usuarios, limpieza_de_hoy):
    id_actividad = limpieza_de_hoy["id_actividad"]

    observacion = exigir(api_voluntario.post(f"/api/actividades/{id_actividad}/observaciones", json=_observacion()), 201)

    assert observacion["id_actividad"] == id_actividad
    assert observacion["id_usuario"] == usuarios["voluntario"].id_usuario
    assert observacion["genera_alerta"] is True


@pytest.mark.parametrize(
    "categoria, severidad, alerta",
    [
        ("recinto", "alto", False),
        ("comportamiento", "bajo", False),
        ("estado_fisico", "medio", True),
    ],
)
def test_solo_algunas_observaciones_generan_alerta(api_manejo, limpieza_de_hoy, categoria, severidad, alerta):
    ruta = f"/api/actividades/{limpieza_de_hoy['id_actividad']}/observaciones"

    observacion = exigir(api_manejo.post(ruta, json=_observacion(categoria=categoria, severidad=severidad)), 201)

    assert observacion["genera_alerta"] is alerta


def test_listar_observaciones_de_una_actividad_y_por_fechas(api_voluntario, limpieza_de_hoy):
    id_actividad = limpieza_de_hoy["id_actividad"]
    creada = exigir(api_voluntario.post(f"/api/actividades/{id_actividad}/observaciones", json=_observacion()), 201)

    de_la_actividad = exigir(api_voluntario.get(f"/api/actividades/{id_actividad}/observaciones"))
    por_fechas = exigir(
        api_voluntario.get("/api/actividades/observaciones", params={"fecha_desde": iso(en_dias(-1)), "fecha_hasta": iso(en_dias(1))})
    )

    assert [o["id_observacion"] for o in de_la_actividad] == [creada["id_observacion"]]
    assert creada["id_observacion"] in [o["id_observacion"] for o in por_fechas]


@pytest.mark.parametrize("cambios", [{"detalle": "corto"}, {"categoria": "otra"}, {"severidad": "extrema"}])
def test_observacion_invalida_422(api_voluntario, limpieza_de_hoy, cambios):
    ruta = f"/api/actividades/{limpieza_de_hoy['id_actividad']}/observaciones"

    assert api_voluntario.post(ruta, json=_observacion(**cambios)).status_code == 422


def test_observacion_de_una_actividad_inexistente_404(api_voluntario):
    assert api_voluntario.post("/api/actividades/2147483647/observaciones", json=_observacion()).status_code == 404


def test_veterinaria_no_registra_observaciones_403(api_veterinaria, limpieza_de_hoy):
    ruta = f"/api/actividades/{limpieza_de_hoy['id_actividad']}/observaciones"

    assert api_veterinaria.post(ruta, json=_observacion()).status_code == 403


# ---------- Referencias para Planificación ----------

def test_referencias_para_los_roles_de_planificacion(api_voluntario, animal, usuarios):
    referencias = exigir(api_voluntario.get("/api/actividades/referencias"))

    assert animal["id_animal"] in [a["id_animal"] for a in referencias["animales"]]
    texto = str(referencias)
    assert "password" not in texto
    assert usuarios["manejo"].correo not in texto
