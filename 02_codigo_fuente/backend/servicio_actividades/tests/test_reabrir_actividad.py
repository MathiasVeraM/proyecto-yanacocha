"""Asume POST /api/actividades/{id_actividad}/reabrir para actividades completadas."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.repositorios.actividad_repo import ActividadRepository

TIPOS_ACTIVIDAD = [
    "actividad_alimentacion",
    "actividad_enriquecimiento",
    "actividad_entrenamiento",
    "actividad_limpieza",
]


def _url(id_actividad, accion):
    return f"/api/actividades/{id_actividad}/{accion}"


@pytest.mark.parametrize("fixture_actividad", TIPOS_ACTIVIDAD)
def test_reabrir_limpia_datos_de_completado_y_conserva_observaciones(
    client, request, fixture_actividad
):
    actividad = request.getfixturevalue(fixture_actividad)
    id_actividad = actividad["id_actividad"]
    completada = client.patch(
        _url(id_actividad, "completar"),
        json={"observaciones": "Se completó sin novedades"},
    )
    assert completada.status_code == 200

    respuesta = client.post(_url(id_actividad, "reabrir"))

    assert respuesta.status_code == 200
    resultado = respuesta.json()
    assert resultado["id_actividad"] == id_actividad
    assert resultado["tipo_actividad"] == actividad["tipo_actividad"]
    assert resultado["completada"] is False
    assert resultado["id_usuario_completo"] is None
    assert resultado["fecha_completada"] is None
    assert resultado["observaciones"] == "Se completó sin novedades"
    assert set(resultado) == set(completada.json())


def test_actividad_reabierta_se_puede_completar_de_nuevo(client, actividad_limpieza):
    id_actividad = actividad_limpieza["id_actividad"]
    client.patch(_url(id_actividad, "completar"), json={})
    client.post(_url(id_actividad, "reabrir"))

    respuesta = client.patch(_url(id_actividad, "completar"), json={})

    assert respuesta.status_code == 200
    assert respuesta.json()["completada"] is True


def test_reabrir_actividad_pendiente_devuelve_409(client, actividad_entrenamiento):
    respuesta = client.post(_url(actividad_entrenamiento["id_actividad"], "reabrir"))

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "La actividad no está completada"


def test_reabrir_actividad_inexistente_devuelve_404(client):
    respuesta = client.post(_url(999999, "reabrir"))

    assert respuesta.status_code == 404


def test_reabrir_sin_token_devuelve_401(client, actividad_limpieza):
    respuesta = client.post(
        _url(actividad_limpieza["id_actividad"], "reabrir"),
        headers={"Authorization": ""},
    )

    assert respuesta.status_code == 401


def test_repositorio_reabrir_hace_rollback_si_falla_la_base():
    db = MagicMock()
    db.commit.side_effect = SQLAlchemyError("fallo")

    with pytest.raises(SQLAlchemyError):
        ActividadRepository.reabrir(db, MagicMock())

    db.rollback.assert_called_once()
