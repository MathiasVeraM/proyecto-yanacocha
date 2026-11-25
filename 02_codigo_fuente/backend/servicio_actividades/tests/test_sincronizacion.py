"""Asume POST /api/actividades/sincronizar y la hora del dispositivo en completar/observaciones."""

from datetime import datetime, timedelta

URL = "/api/actividades/sincronizar"
DETALLE = "El animal se mostró inquieto durante la actividad."


def _completada(actividad, **extra):
    # AHORA_PRUEBAS (conftest) fija "ahora" en 08:00; el móvil marcó unos minutos antes.
    return {
        "id_actividad": actividad["id_actividad"],
        "fecha_completada": f"{actividad['fecha_programada']}T07:55:00",
        **extra,
    }


def _observacion(actividad, id_cliente="uuid-cliente-0001", **extra):
    return {
        "id_cliente": id_cliente,
        "id_actividad": actividad["id_actividad"],
        "categoria": "comportamiento",
        "severidad": "alto",
        "detalle": DETALLE,
        "fecha_registro": f"{actividad['fecha_programada']}T07:56:00",
        **extra,
    }


def test_sincronizar_completa_con_la_hora_del_dispositivo(client, actividad_limpieza, usuario_prueba):
    respuesta = client.post(URL, json={"completadas": [_completada(actividad_limpieza)]})

    assert respuesta.status_code == 200
    assert respuesta.json()["completadas"][0]["resultado"] == "creada"
    guardada = client.get(f"/api/actividades/{actividad_limpieza['id_actividad']}").json()
    assert guardada["completada"] is True
    assert guardada["fecha_completada"].startswith(f"{actividad_limpieza['fecha_programada']}T07:55")
    assert guardada["id_usuario_completo"] == usuario_prueba["id_usuario"]


def test_reenviar_el_mismo_lote_no_duplica(client, actividad_limpieza, actividad_entrenamiento):
    lote = {
        "completadas": [_completada(actividad_limpieza)],
        "observaciones": [_observacion(actividad_entrenamiento)],
    }
    primero = client.post(URL, json=lote).json()
    segundo = client.post(URL, json=lote).json()

    assert primero["completadas"][0]["resultado"] == "creada"
    assert primero["observaciones"][0]["resultado"] == "creada"
    assert segundo["completadas"][0]["resultado"] == "duplicada"
    assert segundo["observaciones"][0]["resultado"] == "duplicada"
    observaciones = client.get(
        f"/api/actividades/{actividad_entrenamiento['id_actividad']}/observaciones"
    ).json()
    assert len(observaciones) == 1
    assert observaciones[0]["genera_alerta"] is True
    assert observaciones[0]["id_cliente"] == "uuid-cliente-0001"
    assert observaciones[0]["fecha_registro"].startswith(
        f"{actividad_entrenamiento['fecha_programada']}T07:56"
    )


def test_un_registro_invalido_no_bloquea_a_los_demas(client, actividad_limpieza):
    lote = {
        "completadas": [
            {"id_actividad": 999999, "fecha_completada": "2026-01-02T08:00:00"},
            _completada(actividad_limpieza),
        ]
    }
    resultado = client.post(URL, json=lote).json()["completadas"]

    assert resultado[0]["resultado"] == "rechazada"
    assert resultado[1]["resultado"] == "creada"


def test_observacion_de_actividad_borrada_se_rechaza(client):
    resultado = client.post(
        URL,
        json={
            "observaciones": [
                {
                    "id_cliente": "uuid-cliente-0002",
                    "id_actividad": 999999,
                    "categoria": "recinto",
                    "severidad": "bajo",
                    "detalle": DETALLE,
                    "fecha_registro": "2026-01-02T08:00:00",
                }
            ]
        },
    ).json()["observaciones"][0]

    assert resultado["resultado"] == "rechazada"


def test_la_hora_del_dispositivo_no_puede_ser_futura(client, actividad_limpieza):
    futura = (datetime(2026, 1, 2, 8, 0) + timedelta(hours=3)).isoformat()
    resultado = client.post(
        URL,
        json={"completadas": [{"id_actividad": actividad_limpieza["id_actividad"], "fecha_completada": futura}]},
    ).json()["completadas"][0]

    assert resultado["resultado"] == "rechazada"
    assert "futura" in resultado["detalle"]


def test_observacion_de_baja_severidad_o_recinto_no_genera_alerta(client, actividad_limpieza):
    client.post(
        URL,
        json={
            "observaciones": [
                _observacion(actividad_limpieza, "uuid-cliente-0003", categoria="recinto", severidad="alto"),
                _observacion(actividad_limpieza, "uuid-cliente-0004", severidad="bajo"),
            ]
        },
    )
    observaciones = client.get(
        f"/api/actividades/{actividad_limpieza['id_actividad']}/observaciones"
    ).json()

    assert len(observaciones) == 2
    assert not any(o["genera_alerta"] for o in observaciones)


def test_voluntario_puede_sincronizar_y_veterinaria_no(client, headers_rol, actividad_limpieza):
    lote = {"completadas": [_completada(actividad_limpieza)]}

    voluntario = client.post(URL, json=lote, headers=headers_rol(4))
    veterinaria = client.post(URL, json=lote, headers=headers_rol(2))

    assert voluntario.status_code == 200
    assert veterinaria.status_code == 403
