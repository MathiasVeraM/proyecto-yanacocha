"""f) Dietas y tomas: crear una dieta, generar sus tomas y comprobar que aparecen como actividades."""
import pytest

from ayudas import en_dias, exigir, iso, unico


def _generar_tomas(api, id_dieta: int, **extra) -> list[dict]:
    return exigir(api.post("/api/actividades/tomas/generar", json={"id_dieta": id_dieta, **extra}))["tomas"]


def _tomas_del_animal(api, id_animal: int) -> list[dict]:
    return exigir(api.get("/api/actividades", params={"id_animal": id_animal, "tipo_actividad": "alimentacion"}))


@pytest.fixture
def otro_animal(api_manejo, taxonomia):
    recinto = exigir(api_manejo.post("/api/animales/recintos", json={"nombre_recinto": unico("Recinto IT")}), 201)
    return exigir(
        api_manejo.post(
            "/api/animales",
            json={"id_taxonomia": taxonomia["id_taxonomia"], "id_recinto": recinto["id_recinto"], "edad_anios": 1, "edad_meses": 0},
        ),
        201,
    )


# ---------- Crear dietas ----------

def test_crear_dieta(crear_dieta, animal, usuarios):
    dieta = exigir(crear_dieta(animal["id_animal"], fin=en_dias(3)), 201)

    assert dieta["id_animal"] == animal["id_animal"]
    assert dieta["vigente"] is True
    assert dieta["id_usuario_creador"] == usuarios["manejo"].id_usuario
    assert dieta["fecha_inicio"] == iso(en_dias(1))
    assert dieta["fecha_fin"] == iso(en_dias(3))
    assert [(a["nombre_alimento"], a["cantidad_gramos"]) for a in dieta["alimentos"]] == [("Pollo", 250.0)]


def test_consultar_dietas(api_voluntario, crear_dieta, animal):
    dieta = exigir(crear_dieta(animal["id_animal"]), 201)

    vigente = exigir(api_voluntario.get(f"/api/actividades/animales/{animal['id_animal']}/dietas/vigente"))
    del_animal = exigir(api_voluntario.get(f"/api/actividades/animales/{animal['id_animal']}/dietas"))
    todas = exigir(api_voluntario.get("/api/actividades/dietas"))
    por_id = exigir(api_voluntario.get(f"/api/actividades/dietas/{dieta['id_dieta']}"))

    assert vigente["id_dieta"] == dieta["id_dieta"]
    assert [d["id_dieta"] for d in del_animal] == [dieta["id_dieta"]]
    assert dieta["id_dieta"] in [d["id_dieta"] for d in todas]
    assert por_id["id_dieta"] == dieta["id_dieta"]


def test_un_animal_sin_dieta_no_tiene_dieta_vigente(api_manejo, animal):
    assert api_manejo.get(f"/api/actividades/animales/{animal['id_animal']}/dietas/vigente").status_code == 404


@pytest.mark.parametrize(
    "cambios, codigo",
    [
        ({"alimentos": []}, 422),
        ({"frecuencia_valor": 0}, 422),
        ({"frecuencia_unidad": "minutos"}, 422),
        ({"alimentos": [{"nombre_alimento": "Pollo", "cantidad_gramos": 0}]}, 422),
        ({"fecha_fin": iso(en_dias(-5))}, 422),
        ({"fecha_inicio": iso(en_dias(40))}, 422),
    ],
)
def test_dieta_con_datos_invalidos_422(crear_dieta, animal, cambios, codigo):
    assert crear_dieta(animal["id_animal"], **cambios).status_code == codigo


def test_dieta_de_un_animal_inexistente_404(crear_dieta):
    assert crear_dieta(2147483647).status_code == 404


def test_una_dieta_nueva_debe_empezar_despues_de_la_vigente(crear_dieta, animal):
    exigir(crear_dieta(animal["id_animal"], inicio=en_dias(2)), 201)

    assert crear_dieta(animal["id_animal"], inicio=en_dias(2)).status_code == 422
    assert crear_dieta(animal["id_animal"], inicio=en_dias(1)).status_code == 422


def test_solo_manejo_de_animales_crea_dietas(api_veterinaria, api_voluntario, animal):
    datos = {
        "id_animal": animal["id_animal"],
        "fecha_inicio": iso(en_dias(1)),
        "frecuencia_valor": 1,
        "frecuencia_unidad": "dias",
        "alimentos": [{"nombre_alimento": "Pollo", "cantidad_gramos": 100}],
    }

    assert api_veterinaria.post("/api/actividades/dietas", json=datos).status_code == 403
    assert api_voluntario.post("/api/actividades/dietas", json=datos).status_code == 403


# ---------- Tomas ----------

def test_generar_tomas_diarias(api_manejo, crear_dieta, animal):
    dieta = exigir(crear_dieta(animal["id_animal"], inicio=en_dias(1), fin=en_dias(3)), 201)

    tomas = _generar_tomas(api_manejo, dieta["id_dieta"])

    assert [t["fecha_programada"] for t in tomas] == [iso(en_dias(1)), iso(en_dias(2)), iso(en_dias(3))]
    for toma in tomas:
        assert toma["tipo_actividad"] == "alimentacion"
        assert toma["id_dieta"] == dieta["id_dieta"]
        assert toma["id_animal"] == animal["id_animal"]
        assert toma["hora_programada"] == "08:00:00"
        assert toma["completada"] is False


def test_las_tomas_aparecen_como_actividades_y_en_el_calendario(api_voluntario, api_manejo, crear_dieta, animal):
    dieta = exigir(crear_dieta(animal["id_animal"], fin=en_dias(3)), 201)
    ids = sorted(t["id_actividad"] for t in _generar_tomas(api_manejo, dieta["id_dieta"]))

    actividades = _tomas_del_animal(api_voluntario, animal["id_animal"])
    calendario = exigir(api_voluntario.get("/api/actividades/calendario", params={"id_animal": animal["id_animal"]}))

    assert sorted(a["id_actividad"] for a in actividades) == ids
    assert sorted(e["id_actividad"] for e in calendario) == ids
    assert {e["tipo"] for e in calendario} == {"alimentacion"}
    assert not any(e["todo_el_dia"] for e in calendario)


def test_generar_tomas_dos_veces_no_las_duplica(api_manejo, crear_dieta, animal):
    dieta = exigir(crear_dieta(animal["id_animal"], fin=en_dias(3)), 201)

    primera = _generar_tomas(api_manejo, dieta["id_dieta"])
    segunda = _generar_tomas(api_manejo, dieta["id_dieta"])

    assert [t["id_actividad"] for t in primera] == [t["id_actividad"] for t in segunda]
    assert len(_tomas_del_animal(api_manejo, animal["id_animal"])) == 3


def test_tomas_cada_12_horas(api_manejo, crear_dieta, animal):
    dieta = exigir(crear_dieta(animal["id_animal"], inicio=en_dias(1), fin=en_dias(1), valor=12, unidad="horas"), 201)

    tomas = _generar_tomas(api_manejo, dieta["id_dieta"])

    assert [(t["fecha_programada"], t["hora_programada"]) for t in tomas] == [
        (iso(en_dias(1)), "08:00:00"),
        (iso(en_dias(1)), "20:00:00"),
    ]


def test_generar_tomas_de_una_dieta_inexistente_404(api_manejo):
    assert api_manejo.post("/api/actividades/tomas/generar", json={"id_dieta": 2147483647}).status_code == 404


def test_solo_manejo_de_animales_genera_tomas(api_voluntario, api_manejo, crear_dieta, animal):
    dieta = exigir(crear_dieta(animal["id_animal"], fin=en_dias(2)), 201)

    assert api_voluntario.post("/api/actividades/tomas/generar", json={"id_dieta": dieta["id_dieta"]}).status_code == 403


def test_extender_la_fecha_de_fin_genera_las_tomas_que_faltan(api_manejo, crear_dieta, animal):
    dieta = exigir(crear_dieta(animal["id_animal"], fin=en_dias(2)), 201)
    _generar_tomas(api_manejo, dieta["id_dieta"])

    extendida = exigir(api_manejo.patch(f"/api/actividades/dietas/{dieta['id_dieta']}", json={"fecha_fin": iso(en_dias(4))}))

    assert extendida["fecha_fin"] == iso(en_dias(4))
    assert len(_tomas_del_animal(api_manejo, animal["id_animal"])) == 4


def test_la_fecha_de_fin_no_puede_ser_anterior_a_hoy(api_manejo, crear_dieta, animal):
    dieta = exigir(crear_dieta(animal["id_animal"], fin=en_dias(2)), 201)

    respuesta = api_manejo.patch(f"/api/actividades/dietas/{dieta['id_dieta']}", json={"fecha_fin": iso(en_dias(-1))})

    assert respuesta.status_code == 422


def test_finalizar_una_dieta(api_manejo, crear_dieta, animal):
    dieta = exigir(crear_dieta(animal["id_animal"], fin=en_dias(4)), 201)
    _generar_tomas(api_manejo, dieta["id_dieta"])

    finalizada = exigir(api_manejo.post(f"/api/actividades/dietas/{dieta['id_dieta']}/finalizar"))

    assert finalizada["vigente"] is False
    assert finalizada["fecha_fin"] is not None
    assert len(_tomas_del_animal(api_manejo, animal["id_animal"])) < 4
    assert api_manejo.post(f"/api/actividades/dietas/{dieta['id_dieta']}/finalizar").status_code == 409
    assert api_manejo.get(f"/api/actividades/animales/{animal['id_animal']}/dietas/vigente").status_code == 404


# ---------- Alimentaciones manuales ----------

def test_una_alimentacion_manual_no_repite_una_toma(api_manejo, programar, crear_dieta, animal):
    dieta = exigir(crear_dieta(animal["id_animal"], fin=en_dias(2)), 201)
    _generar_tomas(api_manejo, dieta["id_dieta"])
    datos = {
        "tipo_actividad": "alimentacion",
        "id_animal": animal["id_animal"],
        "id_dieta": dieta["id_dieta"],
        "fecha_programada": iso(en_dias(1)),
        "hora_programada": "08:00",
    }

    assert programar(datos).status_code == 409
    assert programar({**datos, "hora_programada": "13:00"}).status_code == 201


def test_la_dieta_debe_ser_del_animal_de_la_alimentacion(programar, crear_dieta, animal, otro_animal):
    dieta = exigir(crear_dieta(animal["id_animal"], fin=en_dias(2)), 201)
    datos = {
        "tipo_actividad": "alimentacion",
        "id_animal": otro_animal["id_animal"],
        "id_dieta": dieta["id_dieta"],
        "fecha_programada": iso(en_dias(1)),
        "hora_programada": "13:00",
    }

    assert programar(datos).status_code == 422


def test_la_alimentacion_requiere_dieta(programar, animal):
    datos = {
        "tipo_actividad": "alimentacion",
        "id_animal": animal["id_animal"],
        "fecha_programada": iso(en_dias(1)),
        "hora_programada": "13:00",
    }

    assert programar(datos).status_code == 422
