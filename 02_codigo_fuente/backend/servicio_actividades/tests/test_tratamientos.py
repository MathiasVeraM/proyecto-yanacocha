from datetime import date, datetime, time, timedelta

import pytest

from src.database import Base
from src.logica_negocio import actividad_service


FECHA_BASE = date(2026, 1, 1)
AHORA_FIJA = datetime(2026, 1, 1, 7, 30)


def _crear_tratamiento(
    db,
    animal_id,
    *,
    id_tratamiento=601,
    estado="en_curso",
    frecuencia_valor=1,
    frecuencia_unidad="dias",
    hora_inicio=time(8, 0),
    fecha_inicio=FECHA_BASE,
    fecha_fin=None,
):
    diagnosticos = Base.metadata.tables["gestion_animal.diagnostico"]
    tratamientos = Base.metadata.tables["gestion_animal.tratamiento"]
    id_diagnostico = id_tratamiento + 100
    db.execute(
        diagnosticos.insert().values(
            id_diagnostico=id_diagnostico,
            id_animal=animal_id,
        )
    )
    db.execute(
        tratamientos.insert().values(
            id_tratamiento=id_tratamiento,
            id_diagnostico=id_diagnostico,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            frecuencia_valor=frecuencia_valor,
            frecuencia_unidad=frecuencia_unidad,
            hora_inicio=hora_inicio,
            estado=estado,
        )
    )
    db.commit()
    return id_tratamiento


@pytest.fixture
def ahora_fija(monkeypatch):
    monkeypatch.setattr(actividad_service, "ahora_local", lambda: AHORA_FIJA)


def test_generar_actividades_diarias_por_siete_dias(
    client, db, animal_prueba, ahora_fija
):
    id_tratamiento = _crear_tratamiento(db, animal_prueba["id_animal"])

    respuesta = client.post(
        f"/api/actividades/tratamientos/{id_tratamiento}/generar"
    )

    assert respuesta.status_code == 200
    actividades = respuesta.json()
    assert [actividad["fecha_programada"] for actividad in actividades] == [
        (FECHA_BASE + timedelta(days=dia)).isoformat() for dia in range(7)
    ]
    assert all(actividad["tipo_actividad"] == "tratamiento" for actividad in actividades)
    assert all(actividad["id_tratamiento"] == id_tratamiento for actividad in actividades)


def test_generar_actividades_por_horas(
    client, db, animal_prueba, ahora_fija
):
    id_tratamiento = _crear_tratamiento(
        db,
        animal_prueba["id_animal"],
        frecuencia_valor=12,
        frecuencia_unidad="horas",
    )

    respuesta = client.post(
        f"/api/actividades/tratamientos/{id_tratamiento}/generar"
    )

    assert respuesta.status_code == 200
    horarios = [actividad["hora_programada"] for actividad in respuesta.json()]
    assert horarios[:4] == ["08:00:00", "20:00:00", "08:00:00", "20:00:00"]


def test_generacion_de_tratamiento_es_idempotente(
    client, db, animal_prueba, ahora_fija
):
    id_tratamiento = _crear_tratamiento(db, animal_prueba["id_animal"])
    ruta = f"/api/actividades/tratamientos/{id_tratamiento}/generar"

    primera = client.post(ruta).json()
    segunda = client.post(ruta).json()

    assert [actividad["id_actividad"] for actividad in primera] == [
        actividad["id_actividad"] for actividad in segunda
    ]
    assert len(client.get("/api/actividades", params={"tipo_actividad": "tratamiento"}).json()) == 7


def test_generacion_respeta_fecha_fin(
    client, db, animal_prueba, ahora_fija
):
    id_tratamiento = _crear_tratamiento(
        db,
        animal_prueba["id_animal"],
        fecha_fin=FECHA_BASE + timedelta(days=2),
    )

    respuesta = client.post(
        f"/api/actividades/tratamientos/{id_tratamiento}/generar"
    )

    assert [actividad["fecha_programada"] for actividad in respuesta.json()] == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
    ]


def test_regenerar_elimina_solo_actividades_futuras_pendientes(
    client, db, animal_prueba, ahora_fija
):
    id_tratamiento = _crear_tratamiento(db, animal_prueba["id_animal"])
    ruta = f"/api/actividades/tratamientos/{id_tratamiento}/generar"
    anteriores = client.post(ruta).json()
    completada = client.post(
        f"/api/actividades/{anteriores[0]['id_actividad']}/completar",
        json={},
    ).json()
    db.execute(
        Base.metadata.tables["gestion_animal.tratamiento"]
        .update()
        .where(
            Base.metadata.tables["gestion_animal.tratamiento"].c.id_tratamiento
            == id_tratamiento
        )
        .values(frecuencia_valor=2)
    )
    db.commit()

    regeneradas = client.post(ruta).json()
    restantes = client.get(
        "/api/actividades",
        params={"tipo_actividad": "tratamiento"},
    ).json()

    assert any(
        actividad["id_actividad"] == completada["id_actividad"]
        and actividad["completada"]
        for actividad in restantes
    )
    assert [actividad["fecha_programada"] for actividad in regeneradas] == [
        "2026-01-01",
        "2026-01-03",
        "2026-01-05",
        "2026-01-07",
    ]


def test_tratamiento_sin_frecuencia_no_se_puede_generar(
    client, db, animal_prueba
):
    id_tratamiento = _crear_tratamiento(
        db,
        animal_prueba["id_animal"],
        frecuencia_valor=None,
        frecuencia_unidad=None,
        hora_inicio=None,
    )

    respuesta = client.post(
        f"/api/actividades/tratamientos/{id_tratamiento}/generar"
    )

    assert respuesta.status_code == 422


def test_generar_actividades_de_tratamiento_inexistente_devuelve_404(client):
    respuesta = client.post("/api/actividades/tratamientos/999/generar")
    assert respuesta.status_code == 404

