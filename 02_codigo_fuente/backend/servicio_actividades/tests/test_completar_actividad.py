"""Asume PATCH /api/actividades/{id_actividad}/completar para todos los tipos."""

import pytest

TIPOS_ACTIVIDAD = [
    "actividad_alimentacion",
    "actividad_enriquecimiento",
    "actividad_entrenamiento",
    "actividad_limpieza",
]


@pytest.mark.parametrize("fixture_actividad", TIPOS_ACTIVIDAD)
def test_completar_cada_tipo_registra_usuario_fecha_y_observaciones(
    client, request, fixture_actividad, usuario_prueba
):
    actividad = request.getfixturevalue(fixture_actividad)
    observaciones = "Revisión realizada.\nEl animal respondió bien; mantener seguimiento."

    respuesta = client.patch(
        f"/api/actividades/{actividad['id_actividad']}/completar",
        json={"observaciones": observaciones},
    )

    assert respuesta.status_code == 200
    resultado = respuesta.json()
    assert resultado["completada"] is True
    assert resultado["id_usuario_completo"] == usuario_prueba["id_usuario"]
    assert resultado["fecha_completada"]
    assert resultado["observaciones"] == observaciones


def test_no_completar_sin_usuario_autenticado(client, actividad_entrenamiento):
    respuesta = client.patch(
        f"/api/actividades/{actividad_entrenamiento['id_actividad']}/completar",
        json={},
        headers={"Authorization": ""},
    )

    assert respuesta.status_code == 401


def test_completar_actividad_inexistente_devuelve_404(client):
    respuesta = client.patch("/api/actividades/999999/completar", json={})

    assert respuesta.status_code == 404


def test_completar_actividad_ya_completada_devuelve_conflicto_sin_sobrescribir(
    client, actividad_enriquecimiento
):
    url = f"/api/actividades/{actividad_enriquecimiento['id_actividad']}/completar"
    original = client.patch(url, json={"observaciones": "Registro original"}).json()

    respuesta = client.patch(url, json={"observaciones": "Intento posterior"})

    assert respuesta.status_code == 409
    actual = client.get(f"/api/actividades/{actividad_enriquecimiento['id_actividad']}").json()
    assert actual["id_usuario_completo"] == original["id_usuario_completo"]
    assert actual["fecha_completada"] == original["fecha_completada"]
    assert actual["observaciones"] == "Registro original"


def test_completar_con_observaciones_opcionales(client, actividad_limpieza):
    respuesta = client.patch(
        f"/api/actividades/{actividad_limpieza['id_actividad']}/completar",
        json={},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["observaciones"] is None


def test_actividad_pendiente_inicia_sin_datos_de_completado(actividad_entrenamiento):
    assert actividad_entrenamiento["completada"] is False
    assert actividad_entrenamiento["id_usuario_completo"] is None
    assert actividad_entrenamiento["fecha_completada"] is None
