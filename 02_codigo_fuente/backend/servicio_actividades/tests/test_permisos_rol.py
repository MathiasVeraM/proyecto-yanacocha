"""Permisos por rol en Planificación: qué puede escribir cada rol (las consultas son de todos)."""

import pytest

from src.config import ID_ROL_MANEJO_ANIMAL, ID_ROL_VETERINARIA, ID_ROL_VOLUNTARIO

ID_ROL_ADMIN = 1

DETALLE_VALIDO = "El animal se mostró inquieto durante la actividad."
SIN_PERMISO = "Tu rol no tiene permiso para realizar esta acción"
SOLO_CONSULTA = [ID_ROL_ADMIN, ID_ROL_VETERINARIA]


def _escrituras_de_manejo(id_actividad, id_dieta):
    """Operaciones que solo puede hacer Manejo de Animales: (método, ruta, cuerpo)."""
    return [
        (
            "POST",
            "/api/actividades/enriquecimientos",
            {
                "id_animal": 101,
                "tipo_enriquecimiento": "sensorial",
                "descripcion_estimulo": "Ramas",
                "fecha_programada": "2026-01-03",
                "hora_programada": "10:00:00",
            },
        ),
        ("PUT", f"/api/actividades/{id_actividad}", {"observaciones": "Cambio"}),
        ("DELETE", f"/api/actividades/{id_actividad}", None),
        ("POST", f"/api/actividades/{id_actividad}/reabrir", None),
        ("POST", f"/api/actividades/dietas/{id_dieta}/finalizar", None),
        ("PATCH", f"/api/actividades/dietas/{id_dieta}", {"fecha_fin": None}),
        ("POST", "/api/actividades/tomas/generar", {"id_dieta": id_dieta}),
    ]


@pytest.mark.parametrize("id_rol", [ID_ROL_ADMIN, ID_ROL_VETERINARIA, ID_ROL_VOLUNTARIO])
def test_solo_manejo_crea_edita_elimina_y_maneja_dietas(
    client, headers_rol, actividad_entrenamiento, dieta_con_alimentos, id_rol
):
    headers = headers_rol(id_rol)
    operaciones = _escrituras_de_manejo(
        actividad_entrenamiento["id_actividad"], dieta_con_alimentos["id_dieta"]
    )

    for metodo, ruta, cuerpo in operaciones:
        respuesta = client.request(metodo, ruta, json=cuerpo, headers=headers)
        assert respuesta.status_code == 403, (metodo, ruta)
        assert respuesta.json()["detail"] == SIN_PERMISO

    # Nada cambió: la actividad sigue igual y pendiente
    actual = client.get(f"/api/actividades/{actividad_entrenamiento['id_actividad']}").json()
    assert actual == actividad_entrenamiento


@pytest.mark.parametrize(
    "ruta",
    [
        "/api/actividades",
        "/api/actividades/repetidas",
        "/api/actividades/alimentaciones",
        "/api/actividades/entrenamientos",
        "/api/actividades/limpiezas",
        "/api/actividades/dietas",
    ],
)
def test_voluntario_no_crea_ningun_tipo_de_actividad_ni_dieta(client, headers_rol, ruta):
    respuesta = client.post(ruta, json={}, headers=headers_rol(ID_ROL_VOLUNTARIO))
    assert respuesta.status_code == 403


def test_voluntario_completa_actividades(client, headers_rol, actividad_limpieza):
    respuesta = client.post(
        f"/api/actividades/{actividad_limpieza['id_actividad']}/completar",
        json={"observaciones": "Sin novedades"},
        headers=headers_rol(ID_ROL_VOLUNTARIO),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["completada"] is True


def test_voluntario_registra_observaciones(client, headers_rol, actividad_limpieza):
    respuesta = client.post(
        f"/api/actividades/{actividad_limpieza['id_actividad']}/observaciones",
        json={"categoria": "recinto", "severidad": "bajo", "detalle": DETALLE_VALIDO},
        headers=headers_rol(ID_ROL_VOLUNTARIO),
    )

    assert respuesta.status_code == 201


def test_voluntario_no_reabre_lo_que_completo(client, headers_rol, actividad_limpieza):
    headers = headers_rol(ID_ROL_VOLUNTARIO)
    ruta = f"/api/actividades/{actividad_limpieza['id_actividad']}"
    assert client.post(f"{ruta}/completar", json={}, headers=headers).status_code == 200

    assert client.post(f"{ruta}/reabrir", headers=headers).status_code == 403
    assert client.get(ruta).json()["completada"] is True


@pytest.mark.parametrize("id_rol", SOLO_CONSULTA)
def test_veterinaria_y_administracion_no_completan_ni_observan(
    client, headers_rol, actividad_limpieza, id_rol
):
    headers = headers_rol(id_rol)
    ruta = f"/api/actividades/{actividad_limpieza['id_actividad']}"

    for metodo in ("POST", "PATCH"):
        assert client.request(metodo, f"{ruta}/completar", json={}, headers=headers).status_code == 403
    observacion = {"categoria": "recinto", "severidad": "bajo", "detalle": DETALLE_VALIDO}
    assert client.post(f"{ruta}/observaciones", json=observacion, headers=headers).status_code == 403
    assert client.get(ruta).json()["completada"] is False


@pytest.mark.parametrize("id_rol", [ID_ROL_ADMIN, ID_ROL_VETERINARIA, ID_ROL_MANEJO_ANIMAL, ID_ROL_VOLUNTARIO])
def test_todos_los_roles_consultan_la_planificacion(
    client, headers_rol, actividad_limpieza, id_rol
):
    headers = headers_rol(id_rol)
    id_actividad = actividad_limpieza["id_actividad"]

    assert client.get("/api/actividades", headers=headers).status_code == 200
    assert client.get("/api/actividades/calendario", headers=headers).status_code == 200
    assert client.get(f"/api/actividades/{id_actividad}", headers=headers).status_code == 200
    assert client.get(f"/api/actividades/{id_actividad}/observaciones", headers=headers).status_code == 200
    assert client.get("/api/actividades/dietas", headers=headers).status_code == 200


@pytest.mark.parametrize("id_rol", [ID_ROL_ADMIN, ID_ROL_VETERINARIA, ID_ROL_MANEJO_ANIMAL, ID_ROL_VOLUNTARIO])
@pytest.mark.parametrize("ruta", ["/api/actividades/tomas/renovar", "/api/actividades/tratamientos/renovar"])
def test_cualquier_rol_renueva_el_horizonte(client, headers_rol, id_rol, ruta):
    # Se dispara al abrir Planificación, sin importar quién la abra
    assert client.post(ruta, headers=headers_rol(id_rol)).status_code == 200


@pytest.mark.parametrize("id_rol", [ID_ROL_ADMIN, ID_ROL_VOLUNTARIO])
def test_generar_dosis_de_un_tratamiento_es_de_veterinaria_o_manejo(client, headers_rol, id_rol):
    # Se rechaza por rol antes de buscar el tratamiento
    respuesta = client.post("/api/actividades/tratamientos/999/generar", headers=headers_rol(id_rol))
    assert respuesta.status_code == 403


def test_veterinaria_genera_las_dosis_al_guardar_un_tratamiento(client, headers_rol):
    # Pasa el control de rol (el tratamiento no existe: 404, no 403)
    respuesta = client.post(
        "/api/actividades/tratamientos/999/generar", headers=headers_rol(ID_ROL_VETERINARIA)
    )
    assert respuesta.status_code == 404


@pytest.mark.parametrize("id_rol", [None, "3", [3]])
def test_rol_mal_formado_no_escribe(client, headers_rol, actividad_limpieza, id_rol):
    respuesta = client.post(
        f"/api/actividades/{actividad_limpieza['id_actividad']}/completar",
        json={},
        headers=headers_rol(id_rol),
    )
    assert respuesta.status_code == 403
