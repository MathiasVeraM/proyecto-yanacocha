"""Asume /api/actividades/{id_actividad}/observaciones y GET /api/actividades/observaciones."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.esquemas.observacion_schema import ObservacionCreate
from src.logica_negocio.observacion_service import ObservacionService
from src.repositorios.observacion_repo import ObservacionRepository

DETALLE_VALIDO = "El animal se mostró inquieto durante la actividad."


def _url(id_actividad):
    return f"/api/actividades/{id_actividad}/observaciones"


def _observar(client, id_actividad, categoria="recinto", severidad="bajo", detalle=DETALLE_VALIDO):
    return client.post(
        _url(id_actividad),
        json={"categoria": categoria, "severidad": severidad, "detalle": detalle},
    )


def test_registrar_observacion_devuelve_201_con_datos_del_servidor(
    client, actividad_entrenamiento, usuario_prueba
):
    respuesta = _observar(
        client,
        actividad_entrenamiento["id_actividad"],
        "comportamiento",
        "alto",
        f"   {DETALLE_VALIDO}   ",
    )

    assert respuesta.status_code == 201
    resultado = respuesta.json()
    assert resultado["id_observacion"] > 0
    assert resultado["id_actividad"] == actividad_entrenamiento["id_actividad"]
    assert resultado["categoria"] == "comportamiento"
    assert resultado["severidad"] == "alto"
    assert resultado["detalle"] == DETALLE_VALIDO
    assert resultado["genera_alerta"] is True
    assert resultado["id_usuario"] == usuario_prueba["id_usuario"]
    assert resultado["fecha_registro"]


@pytest.mark.parametrize(
    "categoria,severidad,esperado",
    [
        ("comportamiento", "medio", True),
        ("estado_fisico", "alto", True),
        ("comportamiento", "bajo", False),
        ("recinto", "alto", False),
        ("estado_fisico", "medio", True),
        ("recinto", "medio", False),
        ("estado_fisico", "bajo", False),
    ],
)
def test_genera_alerta_segun_categoria_y_severidad(
    client, actividad_limpieza, categoria, severidad, esperado
):
    respuesta = _observar(client, actividad_limpieza["id_actividad"], categoria, severidad)

    assert respuesta.status_code == 201
    assert respuesta.json()["genera_alerta"] is esperado


def test_observacion_en_actividad_completada_y_varias_por_actividad(
    client, actividad_enriquecimiento
):
    id_actividad = actividad_enriquecimiento["id_actividad"]
    _observar(client, id_actividad, detalle="Primera observación registrada")
    completar = client.patch(f"/api/actividades/{id_actividad}/completar", json={})
    assert completar.status_code == 200

    respuesta = _observar(client, id_actividad, detalle="Segunda observación registrada")

    assert respuesta.status_code == 201
    listado = client.get(_url(id_actividad))
    assert listado.status_code == 200
    assert [item["detalle"] for item in listado.json()] == [
        "Primera observación registrada",
        "Segunda observación registrada",
    ]


def test_registrar_observacion_actividad_inexistente_devuelve_404(client):
    respuesta = _observar(client, 999999)

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Actividad no encontrada"


@pytest.mark.parametrize(
    "cambios",
    [
        {"detalle": "corto"},
        {"detalle": "   abc     "},
        {"detalle": "          "},
        {"categoria": "otra"},
        {"severidad": "critico"},
        {"detalle": None},
    ],
)
def test_registrar_observacion_invalida_devuelve_422(client, actividad_limpieza, cambios):
    datos = {"categoria": "recinto", "severidad": "bajo", "detalle": DETALLE_VALIDO, **cambios}

    respuesta = client.post(_url(actividad_limpieza["id_actividad"]), json=datos)

    assert respuesta.status_code == 422


def test_registrar_observacion_sin_token_devuelve_401(client, actividad_limpieza):
    respuesta = client.post(
        _url(actividad_limpieza["id_actividad"]),
        json={"categoria": "recinto", "severidad": "bajo", "detalle": DETALLE_VALIDO},
        headers={"Authorization": ""},
    )

    assert respuesta.status_code == 401


def test_listar_observaciones_actividad_sin_registros_devuelve_lista_vacia(
    client, actividad_limpieza
):
    respuesta = client.get(_url(actividad_limpieza["id_actividad"]))

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_listar_observaciones_actividad_inexistente_devuelve_404(client):
    respuesta = client.get(_url(999999))

    assert respuesta.status_code == 404


def test_listar_observaciones_de_una_actividad_no_incluye_otras(
    client, actividad_limpieza, actividad_entrenamiento
):
    _observar(client, actividad_limpieza["id_actividad"])
    _observar(client, actividad_entrenamiento["id_actividad"])

    respuesta = client.get(_url(actividad_limpieza["id_actividad"]))

    assert len(respuesta.json()) == 1
    assert respuesta.json()[0]["id_actividad"] == actividad_limpieza["id_actividad"]


def _crear_limpieza(crear_actividad, fecha):
    respuesta = crear_actividad(
        "limpieza",
        fecha_programada=fecha,
        duracion_horas=1,
        duracion_minutos=0,
    )
    assert respuesta.status_code == 201
    return respuesta.json()["id_actividad"]


@pytest.fixture
def observaciones_en_fechas(client, crear_actividad):
    ids = {}
    for fecha in ("2026-03-01", "2026-03-15", "2026-04-01"):
        id_actividad = _crear_limpieza(crear_actividad, fecha)
        assert _observar(client, id_actividad).status_code == 201
        ids[fecha] = id_actividad
    return ids


@pytest.mark.parametrize(
    "params,fechas_esperadas",
    [
        ({}, ["2026-03-01", "2026-03-15", "2026-04-01"]),
        ({"fecha_desde": "2026-03-10"}, ["2026-03-15", "2026-04-01"]),
        ({"fecha_hasta": "2026-03-15"}, ["2026-03-01", "2026-03-15"]),
        ({"fecha_desde": "2026-03-15", "fecha_hasta": "2026-03-15"}, ["2026-03-15"]),
        ({"fecha_desde": "2027-01-01"}, []),
    ],
)
def test_listar_observaciones_por_rango_de_fecha_programada(
    client, observaciones_en_fechas, params, fechas_esperadas
):
    respuesta = client.get("/api/actividades/observaciones", params=params)

    assert respuesta.status_code == 200
    ids_esperados = {observaciones_en_fechas[fecha] for fecha in fechas_esperadas}
    assert {item["id_actividad"] for item in respuesta.json()} == ids_esperados


def test_ruta_observaciones_no_choca_con_obtener_actividad(client, actividad_limpieza):
    # Si /observaciones cayera en GET /{id_actividad} la respuesta sería 422 (id no entero).
    respuesta = client.get("/api/actividades/observaciones")
    detalle = client.get(f"/api/actividades/{actividad_limpieza['id_actividad']}")

    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)
    assert detalle.status_code == 200
    assert detalle.json()["id_actividad"] == actividad_limpieza["id_actividad"]


def test_listar_observaciones_rango_invertido_devuelve_422(client):
    respuesta = client.get(
        "/api/actividades/observaciones",
        params={"fecha_desde": "2026-05-01", "fecha_hasta": "2026-04-01"},
    )

    assert respuesta.status_code == 422


def test_listar_observaciones_fecha_mal_formada_devuelve_422(client):
    respuesta = client.get("/api/actividades/observaciones", params={"fecha_desde": "ayer"})

    assert respuesta.status_code == 422


def test_listar_observaciones_sin_token_devuelve_401(client):
    respuesta = client.get("/api/actividades/observaciones", headers={"Authorization": ""})

    assert respuesta.status_code == 401


def test_eliminar_actividad_elimina_sus_observaciones_en_cascada(
    db, client, actividad_limpieza
):
    from src.modelos.actividad_model import ActividadModel
    from src.modelos.observacion_actividad_model import ObservacionActividadModel

    id_actividad = actividad_limpieza["id_actividad"]
    _observar(client, id_actividad)

    db.query(ActividadModel).filter(ActividadModel.id_actividad == id_actividad).delete()
    db.commit()

    assert db.query(ObservacionActividadModel).count() == 0


# --- Servicio y repositorio (con dependencias simuladas) ---


@pytest.mark.parametrize(
    "categoria,severidad,esperado",
    [
        ("comportamiento", "medio", True),
        ("estado_fisico", "alto", True),
        ("comportamiento", "bajo", False),
        ("recinto", "alto", False),
    ],
)
def test_servicio_calcula_genera_alerta(categoria, severidad, esperado):
    assert ObservacionService.genera_alerta(categoria, severidad) is esperado


def test_servicio_crear_guarda_flag_usuario_y_fecha_local():
    datos = ObservacionCreate(
        categoria="estado_fisico",
        severidad="medio",
        detalle=DETALLE_VALIDO,
    )
    db = MagicMock()
    with (
        patch(
            "src.logica_negocio.observacion_service.ActividadService.actividad_o_404"
        ) as actividad_o_404,
        patch(
            "src.logica_negocio.observacion_service.ObservacionRepository.crear"
        ) as crear,
        patch("src.logica_negocio.observacion_service.ahora_local") as ahora,
    ):
        ObservacionService.crear(db, 7, datos, 301)

    actividad_o_404.assert_called_once_with(db, 7)
    guardado = crear.call_args.args[1]
    assert guardado["genera_alerta"] is True
    assert guardado["id_usuario"] == 301
    assert guardado["fecha_registro"] is ahora.return_value


def test_servicio_crear_actividad_inexistente_no_guarda():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    datos = ObservacionCreate(categoria="recinto", severidad="bajo", detalle=DETALLE_VALIDO)

    with patch(
        "src.logica_negocio.observacion_service.ObservacionRepository.crear"
    ) as crear:
        with pytest.raises(HTTPException) as error:
            ObservacionService.crear(db, 1, datos, 301)

    assert error.value.status_code == 404
    crear.assert_not_called()


def test_servicio_listar_por_fechas_rango_invertido_lanza_422():
    with pytest.raises(HTTPException) as error:
        ObservacionService.listar_por_fechas(MagicMock(), date(2026, 5, 2), date(2026, 5, 1))

    assert error.value.status_code == 422


def test_repositorio_crear_hace_rollback_si_falla_la_base():
    db = MagicMock()
    db.commit.side_effect = SQLAlchemyError("fallo")

    with pytest.raises(SQLAlchemyError):
        ObservacionRepository.crear(
            db,
            {
                "id_actividad": 1,
                "categoria": "recinto",
                "severidad": "bajo",
                "detalle": DETALLE_VALIDO,
                "genera_alerta": False,
                "id_usuario": 301,
            },
        )

    db.rollback.assert_called_once()
