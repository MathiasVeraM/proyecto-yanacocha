"""d) Gestión animal: taxonomía, recintos, animales (código YC-AAAA-NNNN), diagnósticos y tratamientos."""
import re

import pytest

from ayudas import en_dias, exigir, hoy_ec, iso, unico

PATRON_CODIGO = re.compile(r"^YC-(\d{4})-(\d{4})$")


def _datos_animal(taxonomia, recinto, **cambios):
    datos = {
        "id_taxonomia": taxonomia["id_taxonomia"],
        "id_recinto": recinto["id_recinto"],
        "nombre": unico("Ejemplar"),
        "edad_anios": 2,
        "edad_meses": 6,
        "sexo": "hembra",
    }
    datos.update(cambios)
    return datos


# ---------- Taxonomía y recintos ----------

def test_crear_y_buscar_taxonomia(api_manejo):
    nombre = unico("Cóndor de prueba")

    creada = exigir(
        api_manejo.post("/api/animales/taxonomia", json={"nombre_comun": nombre, "especie": unico("Vultur testus"), "clase": "Aves"}),
        201,
    )
    encontrada = exigir(api_manejo.get("/api/animales/taxonomia", params={"buscar": nombre}))

    assert creada["nombre_comun"] == nombre
    assert creada["id_taxonomia"] in [t["id_taxonomia"] for t in encontrada]


def test_taxonomia_sin_nombre_comun_422(api_manejo):
    assert api_manejo.post("/api/animales/taxonomia", json={"especie": "Sin nombre"}).status_code == 422


def test_crear_recinto_queda_disponible_por_defecto(api_manejo):
    creado = exigir(api_manejo.post("/api/animales/recintos", json={"nombre_recinto": unico("Recinto")}), 201)

    assert creado["estado"] == "disponible"
    assert creado["id_recinto"] in [r["id_recinto"] for r in exigir(api_manejo.get("/api/animales/recintos"))]


@pytest.mark.parametrize("cambios", [{"capacidad": 0}, {"estado": "inventado"}, {"nombre_recinto": ""}])
def test_recinto_con_datos_invalidos_422(api_manejo, cambios):
    datos = {"nombre_recinto": unico("Recinto"), **cambios}

    assert api_manejo.post("/api/animales/recintos", json=datos).status_code == 422


def test_no_se_repite_el_nombre_de_un_recinto(api_manejo, recinto):
    respuesta = api_manejo.post("/api/animales/recintos", json={"nombre_recinto": recinto["nombre_recinto"]})

    assert respuesta.status_code in (400, 409)


# ---------- Animales y código YC-AAAA-NNNN ----------

def test_crear_animal_genera_codigo_con_el_anio_de_ecuador(animal):
    coincidencia = PATRON_CODIGO.match(animal["codigo_animal"])

    assert coincidencia, animal["codigo_animal"]
    assert int(coincidencia.group(1)) == hoy_ec().year
    assert animal["estado_actual"] == "en_centro"
    assert animal["fecha_ingreso"] == iso(hoy_ec())


def test_los_codigos_nuevos_siempre_son_mayores(api_manejo, taxonomia, recinto):
    primero = exigir(api_manejo.post("/api/animales", json=_datos_animal(taxonomia, recinto)), 201)
    segundo = exigir(api_manejo.post("/api/animales", json=_datos_animal(taxonomia, recinto)), 201)

    assert primero["codigo_animal"] != segundo["codigo_animal"]
    numero = lambda animal: int(PATRON_CODIGO.match(animal["codigo_animal"]).group(2))  # noqa: E731
    assert numero(segundo) > numero(primero)


def test_el_animal_trae_su_taxonomia_y_su_recinto(animal, taxonomia, recinto):
    assert animal["taxonomia"]["id_taxonomia"] == taxonomia["id_taxonomia"]
    assert animal["recinto"]["id_recinto"] == recinto["id_recinto"]
    assert animal["edad_anios"] == 3
    assert animal["tiene_tratamiento_en_curso"] is False


def test_consultar_y_listar_animales(api_manejo, animal):
    por_id = exigir(api_manejo.get(f"/api/animales/{animal['id_animal']}"))
    listado = exigir(api_manejo.get("/api/animales"))

    assert por_id["codigo_animal"] == animal["codigo_animal"]
    assert animal["id_animal"] in [a["id_animal"] for a in listado]


def test_animal_inexistente_404(api_manejo):
    assert api_manejo.get("/api/animales/2147483647").status_code == 404


def test_editar_animal_conserva_el_codigo(api_manejo, animal):
    editado = exigir(api_manejo.put(f"/api/animales/{animal['id_animal']}", json={"nombre": "Nuevo nombre", "edad_anios": 4}))

    assert editado["nombre"] == "Nuevo nombre"
    assert editado["edad_anios"] == 4
    assert editado["codigo_animal"] == animal["codigo_animal"]


@pytest.mark.parametrize(
    "cambios, codigos",
    [
        ({"id_taxonomia": 2147483647}, (400, 404)),
        ({"id_recinto": 2147483647}, (400, 404)),
        ({"fecha_ingreso": iso(en_dias(5))}, (422,)),
        ({"edad_meses": 12}, (422,)),
        ({"sexo": "otro"}, (422,)),
    ],
)
def test_animal_con_datos_invalidos_se_rechaza(api_manejo, taxonomia, recinto, cambios, codigos):
    respuesta = api_manejo.post("/api/animales", json=_datos_animal(taxonomia, recinto, **cambios))

    assert respuesta.status_code in codigos


def test_animal_sin_edad_422(api_manejo, taxonomia, recinto):
    datos = _datos_animal(taxonomia, recinto)
    del datos["edad_anios"], datos["edad_meses"]

    assert api_manejo.post("/api/animales", json=datos).status_code == 422


# ---------- Diagnósticos ----------

def test_veterinaria_registra_un_diagnostico_a_su_nombre(usuarios, diagnostico, animal):
    assert diagnostico["id_animal"] == animal["id_animal"]
    assert diagnostico["id_usuario"] == usuarios["veterinaria"].id_usuario
    assert diagnostico["es_critico"] is False
    assert diagnostico["fecha_registro"]


def test_listar_y_actualizar_diagnosticos(api_veterinaria, animal, diagnostico):
    listado = exigir(api_veterinaria.get(f"/api/animales/{animal['id_animal']}/diagnosticos"))
    actualizado = exigir(
        api_veterinaria.put(f"/api/animales/diagnosticos/{diagnostico['id_diagnostico']}", json={"es_critico": True})
    )

    assert diagnostico["id_diagnostico"] in [d["id_diagnostico"] for d in listado]
    assert actualizado["es_critico"] is True


def test_diagnostico_vacio_422(api_veterinaria, animal):
    assert api_veterinaria.post(f"/api/animales/{animal['id_animal']}/diagnosticos", json={"diagnostico": ""}).status_code == 422


def test_diagnostico_de_un_animal_inexistente_404(api_veterinaria):
    assert api_veterinaria.post("/api/animales/2147483647/diagnosticos", json={"diagnostico": "Fiebre"}).status_code == 404


# ---------- Tratamientos ----------

def test_crear_tratamiento_con_medicamentos(crear_tratamiento, diagnostico):
    tratamiento = exigir(crear_tratamiento(), 201)

    assert tratamiento["id_diagnostico"] == diagnostico["id_diagnostico"]
    assert tratamiento["estado"] == "en_curso"
    assert tratamiento["fecha_inicio"] == iso(en_dias(1))
    assert tratamiento["frecuencia_valor"] == 1
    assert sorted((m["nombre_medicamento"], m["dosis_ml"]) for m in tratamiento["medicamentos"]) == [
        ("Amoxicilina", 2.5),
        ("Vitamina B", 1.0),
    ]


def test_el_tratamiento_aparece_en_la_ficha_y_marca_al_animal(api_veterinaria, api_manejo, animal, crear_tratamiento):
    # Un tratamiento solo está "en curso" si ya empezó: se programa desde hoy
    creado = exigir(crear_tratamiento(fecha_inicio=iso(hoy_ec())), 201)

    del_animal = exigir(api_veterinaria.get(f"/api/animales/{animal['id_animal']}/tratamientos"))
    ficha = exigir(api_manejo.get(f"/api/animales/{animal['id_animal']}"))
    en_curso = exigir(api_manejo.get("/api/animales/metricas/animales-con-tratamiento-en-curso"))

    assert [t["id_tratamiento"] for t in del_animal] == [creado["id_tratamiento"]]
    assert ficha["tiene_tratamiento_en_curso"] is True
    assert en_curso >= 1


def test_actualizar_y_finalizar_un_tratamiento(api_veterinaria, crear_tratamiento):
    creado = exigir(crear_tratamiento(), 201)

    finalizado = exigir(
        api_veterinaria.put(f"/api/animales/tratamientos/{creado['id_tratamiento']}", json={"estado": "finalizado"})
    )

    assert finalizado["estado"] == "finalizado"
    assert finalizado["fecha_fin"] is not None


@pytest.mark.parametrize(
    "cambios, codigos",
    [
        ({"fecha_inicio": iso(en_dias(-1))}, (422,)),
        ({"fecha_inicio": iso(en_dias(5)), "fecha_fin": iso(en_dias(2))}, (400,)),
        ({"frecuencia_valor": 0}, (422,)),
        ({"frecuencia_unidad": "meses"}, (422,)),
        ({"medicamentos": [{"nombre_medicamento": "X", "dosis_ml": 0}]}, (422,)),
    ],
)
def test_tratamiento_con_datos_invalidos_se_rechaza(crear_tratamiento, cambios, codigos):
    assert crear_tratamiento(**cambios).status_code in codigos


def test_tratamiento_de_un_diagnostico_inexistente_404(api_veterinaria):
    respuesta = api_veterinaria.post(
        "/api/animales/diagnosticos/2147483647/tratamientos",
        json={"descripcion": "x", "frecuencia_valor": 1, "frecuencia_unidad": "dias", "hora_inicio": "09:00:00"},
    )

    assert respuesta.status_code == 404
