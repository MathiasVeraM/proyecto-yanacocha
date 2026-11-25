"""g) Integración entre servicios: Gestión Animal -> Actividades (dosis de tratamientos).

Flujo real de la aplicación: Veterinaria guarda el tratamiento (Gestión Animal) y, con ese mismo token, se le pide
a Gestión Animal que genere las dosis; este llama por HTTP al servicio de Actividades, que las programa.
"""
import time

import pytest

from ayudas import (
    docker_disponible,
    en_dias,
    exigir,
    id_contenedor,
    detener_contenedor,
    iniciar_contenedor,
    iso,
)


def _generar_dosis(api_veterinaria, id_tratamiento: int):
    return api_veterinaria.post(f"/api/animales/tratamientos/{id_tratamiento}/generar-actividades")


def _dosis_del_animal(api, id_animal: int) -> list[dict]:
    return exigir(api.get("/api/actividades", params={"id_animal": id_animal, "tipo_actividad": "tratamiento"}))


@pytest.fixture
def tratamiento(crear_tratamiento):
    return exigir(crear_tratamiento(), 201)


# ---------- Tratamiento -> dosis en Actividades ----------

def test_el_tratamiento_genera_una_dosis_por_dia(api_veterinaria, animal, tratamiento):
    dosis = exigir(_generar_dosis(api_veterinaria, tratamiento["id_tratamiento"]))

    assert [d["fecha_programada"] for d in dosis] == [iso(en_dias(1)), iso(en_dias(2)), iso(en_dias(3))]
    for una in dosis:
        assert una["tipo_actividad"] == "tratamiento"
        assert una["id_tratamiento"] == tratamiento["id_tratamiento"]
        assert una["id_animal"] == animal["id_animal"]
        assert una["hora_programada"] == "09:00:00"
        assert una["completada"] is False
        assert una["descripcion_tratamiento"] == "Antibiótico por tres días"
        assert [(m["nombre_medicamento"], m["dosis_ml"]) for m in una["medicamentos_tratamiento"]] == [
            ("Amoxicilina", 2.5),
            ("Vitamina B", 1.0),
        ]


def test_las_dosis_aparecen_en_actividades_y_en_el_calendario(api_veterinaria, api_voluntario, animal, tratamiento):
    ids = sorted(d["id_actividad"] for d in exigir(_generar_dosis(api_veterinaria, tratamiento["id_tratamiento"])))

    actividades = _dosis_del_animal(api_voluntario, animal["id_animal"])
    calendario = exigir(
        api_voluntario.get("/api/actividades/calendario", params={"id_animal": animal["id_animal"], "tipo_actividad": "tratamiento"})
    )

    assert sorted(a["id_actividad"] for a in actividades) == ids
    assert sorted(e["id_actividad"] for e in calendario) == ids
    assert {e["tipo"] for e in calendario} == {"tratamiento"}
    assert [e["inicio"] for e in calendario] == [f"{iso(en_dias(n))}T09:00:00" for n in (1, 2, 3)]


def test_generar_las_dosis_dos_veces_no_las_duplica(api_veterinaria, api_manejo, animal, tratamiento):
    primera = exigir(_generar_dosis(api_veterinaria, tratamiento["id_tratamiento"]))
    segunda = exigir(_generar_dosis(api_veterinaria, tratamiento["id_tratamiento"]))

    assert [d["id_actividad"] for d in primera] == [d["id_actividad"] for d in segunda]
    assert len(_dosis_del_animal(api_manejo, animal["id_animal"])) == 3


def test_las_dosis_se_cambian_desde_el_tratamiento_no_desde_planificacion(api_veterinaria, api_manejo, tratamiento):
    dosis = exigir(_generar_dosis(api_veterinaria, tratamiento["id_tratamiento"]))

    respuesta = api_manejo.put(f"/api/actividades/{dosis[0]['id_actividad']}", json={"observaciones": "cambio"})

    assert respuesta.status_code == 409


def test_suspender_el_tratamiento_retira_las_dosis_pendientes(api_veterinaria, api_manejo, animal, tratamiento):
    exigir(_generar_dosis(api_veterinaria, tratamiento["id_tratamiento"]))
    exigir(api_veterinaria.put(f"/api/animales/tratamientos/{tratamiento['id_tratamiento']}", json={"estado": "suspendido"}))

    dosis = exigir(_generar_dosis(api_veterinaria, tratamiento["id_tratamiento"]))

    assert dosis == []
    assert _dosis_del_animal(api_manejo, animal["id_animal"]) == []


def test_el_tratamiento_inexistente_404(api_veterinaria):
    assert _generar_dosis(api_veterinaria, 2147483647).status_code == 404


def test_solo_veterinaria_genera_dosis_desde_fichas(api_manejo, api_voluntario, tratamiento):
    ruta = f"/api/animales/tratamientos/{tratamiento['id_tratamiento']}/generar-actividades"

    assert api_manejo.post(ruta).status_code == 403
    assert api_voluntario.post(ruta).status_code == 403


def test_veterinaria_no_llama_directo_a_actividades_por_el_gateway(api_veterinaria, tratamiento):
    # No tiene el módulo de planificación: solo Gestión Animal (con su token) puede pedir las dosis
    ruta = f"/api/actividades/tratamientos/{tratamiento['id_tratamiento']}/generar"

    assert api_veterinaria.post(ruta).status_code == 403


# ---------- Actividades no disponible ----------

@pytest.fixture
def actividades_detenido(docker_requerido, api_manejo):
    """Detiene el contenedor de Actividades y, pase lo que pase, lo vuelve a levantar al terminar."""
    detener_contenedor("actividades")

    def reiniciar():
        iniciar_contenedor("actividades")
        # El gateway puede conservar una conexión vieja: se espera a que vuelva a responder
        for _ in range(30):
            if api_manejo.get("/api/actividades/limites").status_code == 200:
                return
            time.sleep(1)
        raise AssertionError("El gateway no volvió a alcanzar el servicio de actividades")

    yield reiniciar
    if id_contenedor("actividades") and docker_disponible():
        iniciar_contenedor("actividades")


@pytest.mark.destructivo
@pytest.mark.requiere_docker
def test_si_actividades_cae_el_tratamiento_se_guarda_igual(
    api_veterinaria, api_manejo, animal, crear_tratamiento, actividades_detenido
):
    # El tratamiento se guarda aunque Actividades no responda
    guardado = exigir(crear_tratamiento(), 201)
    en_la_ficha = exigir(api_veterinaria.get(f"/api/animales/{animal['id_animal']}/tratamientos"))
    assert [t["id_tratamiento"] for t in en_la_ficha] == [guardado["id_tratamiento"]]

    # Generar las dosis falla de forma controlada (503), no con un error interno
    fallida = _generar_dosis(api_veterinaria, guardado["id_tratamiento"])
    assert fallida.status_code == 503
    assert "actividades" in fallida.json()["detail"]

    # El gateway también avisa que el servicio no está disponible
    assert api_manejo.get("/api/actividades").status_code == 503

    # Al volver Actividades, se pueden generar las dosis del tratamiento que quedó guardado
    actividades_detenido()
    dosis = exigir(_generar_dosis(api_veterinaria, guardado["id_tratamiento"]))
    assert len(dosis) == 3
