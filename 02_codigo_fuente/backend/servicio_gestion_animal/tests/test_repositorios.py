from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from src.modelos.animal_model import ahora_local, hoy_local
from src.repositorios.animal_repo import AnimalRepository
from src.repositorios.diagnostico_repo import DiagnosticoRepository
from src.repositorios.tratamiento_repo import TratamientoRepository


def test_fechas_locales_estan_en_hora_de_ecuador():
    # Ecuador es UTC-5 todo el año (no tiene horario de verano)
    diferencia = datetime.now(timezone.utc).replace(tzinfo=None) - ahora_local()
    assert abs(diferencia - timedelta(hours=5)) < timedelta(minutes=1)
    assert hoy_local() == ahora_local().date()


def _datos_animal(codigo="YNC-010"):
    return dict(codigo_animal=codigo, nombre_comun="Cóndor andino", especie="Vultur gryphus")


# ---------- Animal ----------

def test_animal_crear_con_valores_por_defecto(db):
    animal = AnimalRepository.crear_animal(db, _datos_animal())
    assert animal.id_animal is not None
    assert animal.estado_actual == "en_centro"
    assert animal.fecha_ingreso == hoy_local()


def test_animal_consultar(db):
    animal = AnimalRepository.crear_animal(db, _datos_animal())
    assert AnimalRepository.obtener_por_id(db, animal.id_animal).codigo_animal == "YNC-010"
    assert AnimalRepository.obtener_por_codigo(db, "YNC-010").id_animal == animal.id_animal


def test_animal_inexistente_devuelve_none(db):
    assert AnimalRepository.obtener_por_id(db, 999) is None
    assert AnimalRepository.obtener_por_codigo(db, "NO-EXISTE") is None


def test_animal_listar_ordenado_por_codigo(db, crear_animal_db):
    crear_animal_db(codigo_animal="YNC-003")
    crear_animal_db(codigo_animal="YNC-001")
    codigos = [a.codigo_animal for a in AnimalRepository.obtener_todos(db)]
    assert codigos == ["YNC-001", "YNC-003"]


def test_animal_actualizar(db, crear_animal_db):
    animal = crear_animal_db()
    animal = AnimalRepository.actualizar_animal(db, animal, {"estado_actual": "liberado", "sexo": "hembra"})
    assert (animal.estado_actual, animal.sexo) == ("liberado", "hembra")


def test_animal_codigo_duplicado_lanza_error(db):
    AnimalRepository.crear_animal(db, _datos_animal())
    with pytest.raises(IntegrityError):
        AnimalRepository.crear_animal(db, _datos_animal())


# ---------- Diagnóstico ----------

def test_diagnostico_crear_con_valores_por_defecto(db, crear_animal_db, id_veterinario):
    animal = crear_animal_db()
    diagnostico = DiagnosticoRepository.crear_diagnostico(db, {
        "id_animal": animal.id_animal,
        "id_usuario": id_veterinario,
        "diagnostico": "Fractura en ala izquierda",
    })
    assert diagnostico.id_diagnostico is not None
    assert diagnostico.es_critico is False
    # Se guarda en hora de Ecuador, no en la hora UTC del servidor
    assert abs(diagnostico.fecha_registro - ahora_local()) < timedelta(minutes=1)


def test_diagnostico_consultar_por_id(db, crear_animal_db, crear_diagnostico_db):
    diagnostico = crear_diagnostico_db(crear_animal_db().id_animal)
    assert DiagnosticoRepository.obtener_por_id(db, diagnostico.id_diagnostico).diagnostico == "Deshidratación leve"
    assert DiagnosticoRepository.obtener_por_id(db, 999) is None


def test_diagnostico_listar_solo_los_del_animal(db, crear_animal_db, crear_diagnostico_db):
    oso = crear_animal_db(codigo_animal="YNC-001")
    condor = crear_animal_db(codigo_animal="YNC-002")
    primero = crear_diagnostico_db(oso.id_animal, diagnostico="Primero")
    segundo = crear_diagnostico_db(oso.id_animal, diagnostico="Segundo")
    crear_diagnostico_db(condor.id_animal, diagnostico="De otro animal")

    ids = [d.id_diagnostico for d in DiagnosticoRepository.obtener_por_animal(db, oso.id_animal)]
    # Los más recientes primero
    assert ids == [segundo.id_diagnostico, primero.id_diagnostico]


def test_diagnostico_de_animal_inexistente_lanza_error(db, id_veterinario):
    with pytest.raises(IntegrityError):
        DiagnosticoRepository.crear_diagnostico(db, {
            "id_animal": 999, "id_usuario": id_veterinario, "diagnostico": "X",
        })


# ---------- Tratamiento ----------

def test_tratamiento_crear_con_valores_por_defecto(db, crear_animal_db, crear_diagnostico_db):
    diagnostico = crear_diagnostico_db(crear_animal_db().id_animal)
    tratamiento = TratamientoRepository.crear_tratamiento(db, {
        "id_diagnostico": diagnostico.id_diagnostico,
        "medicamento_o_proceso": "Suero oral",
        "dosis": "50 ml",
        "frecuencia": "cada 8 h",
    })
    assert tratamiento.id_tratamiento is not None
    assert tratamiento.estado == "en_curso"
    assert tratamiento.fecha_inicio == hoy_local()
    assert tratamiento.fecha_fin is None


def test_tratamiento_consultar_y_listar(db, crear_animal_db, crear_diagnostico_db):
    animal = crear_animal_db()
    diagnostico = crear_diagnostico_db(animal.id_animal)
    otro = crear_diagnostico_db(animal.id_animal, diagnostico="Otro")
    tratamiento = TratamientoRepository.crear_tratamiento(db, {
        "id_diagnostico": diagnostico.id_diagnostico, "medicamento_o_proceso": "Antibiótico",
    })
    TratamientoRepository.crear_tratamiento(db, {
        "id_diagnostico": otro.id_diagnostico, "medicamento_o_proceso": "Vendaje",
    })

    assert TratamientoRepository.obtener_por_id(db, tratamiento.id_tratamiento).medicamento_o_proceso == "Antibiótico"
    assert TratamientoRepository.obtener_por_id(db, 999) is None
    lista = TratamientoRepository.obtener_por_diagnostico(db, diagnostico.id_diagnostico)
    assert [t.id_tratamiento for t in lista] == [tratamiento.id_tratamiento]


def test_tratamiento_actualizar(db, crear_animal_db, crear_diagnostico_db):
    diagnostico = crear_diagnostico_db(crear_animal_db().id_animal)
    tratamiento = TratamientoRepository.crear_tratamiento(db, {
        "id_diagnostico": diagnostico.id_diagnostico, "medicamento_o_proceso": "Antibiótico",
    })
    tratamiento = TratamientoRepository.actualizar_tratamiento(
        db, tratamiento, {"estado": "finalizado", "fecha_fin": hoy_local()}
    )
    assert (tratamiento.estado, tratamiento.fecha_fin) == ("finalizado", hoy_local())


def test_tratamiento_de_diagnostico_inexistente_lanza_error(db):
    with pytest.raises(IntegrityError):
        TratamientoRepository.crear_tratamiento(db, {
            "id_diagnostico": 999, "medicamento_o_proceso": "X",
        })
