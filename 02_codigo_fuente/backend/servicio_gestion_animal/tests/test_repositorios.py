from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from src.modelos.fechas import ahora_local, hoy_local
from src.repositorios.animal_repo import AnimalRepository
from src.repositorios.diagnostico_repo import DiagnosticoRepository
from src.repositorios.recinto_repo import RecintoRepository
from src.repositorios.taxonomia_repo import TaxonomiaRepository
from src.repositorios.tratamiento_repo import TratamientoRepository


def test_fechas_locales_estan_en_hora_de_ecuador():
    # Ecuador es UTC-5 todo el año (no tiene horario de verano)
    diferencia = datetime.now(timezone.utc).replace(tzinfo=None) - ahora_local()
    assert abs(diferencia - timedelta(hours=5)) < timedelta(minutes=1)
    assert hoy_local() == ahora_local().date()


# ---------- Taxonomía ----------

def test_taxonomia_crear_y_consultar(db):
    t = TaxonomiaRepository.crear_taxonomia(db, {
        "nombre_comun": "Perro", "especie": "Canis lupus familiaris", "genero": "Canis", "familia": "Canidae",
    })
    assert TaxonomiaRepository.obtener_por_id(db, t.id_taxonomia).especie == "Canis lupus familiaris"
    assert TaxonomiaRepository.obtener_por_id(db, 999) is None


def test_taxonomia_nombre_comun_sin_distinguir_mayusculas(db, crear_taxonomia_db):
    perro = crear_taxonomia_db(nombre_comun="Perro", especie="Canis lupus familiaris")
    assert TaxonomiaRepository.obtener_por_nombre_comun(db, "PERRO").id_taxonomia == perro.id_taxonomia
    assert TaxonomiaRepository.obtener_por_nombre_comun(db, "gato") is None


def test_taxonomia_nombre_comun_repetido_lanza_error(db, crear_taxonomia_db):
    crear_taxonomia_db(nombre_comun="Perro", especie="Canis lupus familiaris")
    with pytest.raises(IntegrityError):
        TaxonomiaRepository.crear_taxonomia(db, {"nombre_comun": "perro", "especie": "Otra"})


def test_taxonomia_buscar_por_nombre_comun_o_cientifico(db, crear_taxonomia_db):
    crear_taxonomia_db(nombre_comun="Oso de anteojos", especie="Tremarctos ornatus")
    crear_taxonomia_db(nombre_comun="Cóndor andino", especie="Vultur gryphus")
    assert [t.nombre_comun for t in TaxonomiaRepository.buscar(db, "oso")] == ["Oso de anteojos"]
    assert [t.nombre_comun for t in TaxonomiaRepository.buscar(db, "vultur")] == ["Cóndor andino"]
    assert len(TaxonomiaRepository.buscar(db)) == 2
    assert len(TaxonomiaRepository.buscar(db, limite=1)) == 1


def test_taxonomia_por_id_inaturalist(db, crear_taxonomia_db):
    crear_taxonomia_db(id_inaturalist=41657)
    assert TaxonomiaRepository.obtener_por_id_inaturalist(db, 41657) is not None
    assert TaxonomiaRepository.obtener_por_id_inaturalist(db, 1) is None
    assert TaxonomiaRepository.obtener_ids_inaturalist(db, [41657, 1]) == {41657}
    assert TaxonomiaRepository.obtener_ids_inaturalist(db, []) == set()


def test_taxonomia_actualizar(db, crear_taxonomia_db):
    t = crear_taxonomia_db()
    t = TaxonomiaRepository.actualizar_taxonomia(db, t, {"familia": "Ursidae (osos)"})
    assert t.familia == "Ursidae (osos)"


# ---------- Recinto ----------

def test_recinto_crear_con_estado_por_defecto(db):
    r = RecintoRepository.crear_recinto(db, {"nombre_recinto": "Aviario 1", "tipo": "aviario", "capacidad": 10})
    assert r.estado == "disponible"
    assert RecintoRepository.obtener_por_id(db, r.id_recinto).nombre_recinto == "Aviario 1"
    assert RecintoRepository.obtener_por_nombre(db, "Aviario 1").id_recinto == r.id_recinto
    assert RecintoRepository.obtener_por_id(db, 999) is None


def test_recinto_listar_y_actualizar(db, crear_recinto_db):
    crear_recinto_db(nombre_recinto="Zona B")
    a = crear_recinto_db(nombre_recinto="Zona A")
    assert [r.nombre_recinto for r in RecintoRepository.obtener_todos(db)] == ["Zona A", "Zona B"]
    a = RecintoRepository.actualizar_recinto(db, a, {"estado": "en_limpieza"})
    assert a.estado == "en_limpieza"


def test_recinto_nombre_repetido_lanza_error(db, crear_recinto_db):
    crear_recinto_db(nombre_recinto="Zona A")
    with pytest.raises(IntegrityError):
        RecintoRepository.crear_recinto(db, {"nombre_recinto": "Zona A"})


# ---------- Animal ----------

def test_animal_crear_con_valores_por_defecto(db, crear_taxonomia_db, crear_recinto_db):
    animal = AnimalRepository.crear_animal(db, {
        "codigo_animal": "TO-001",
        "id_taxonomia": crear_taxonomia_db().id_taxonomia,
        "id_recinto": crear_recinto_db().id_recinto,
    })
    assert animal.estado_actual == "en_centro"
    assert animal.fecha_ingreso == hoy_local()
    # La taxonomía y el recinto se cargan con el animal
    assert animal.taxonomia.especie == "Tremarctos ornatus"
    assert animal.recinto.nombre_recinto == "Sector de osos"


def test_animal_sin_taxonomia_o_recinto_validos_lanza_error(db, crear_taxonomia_db, crear_recinto_db):
    with pytest.raises(IntegrityError):
        AnimalRepository.crear_animal(db, {
            "codigo_animal": "X-001", "id_taxonomia": 999, "id_recinto": crear_recinto_db().id_recinto,
        })
    db.rollback()
    with pytest.raises(IntegrityError):
        AnimalRepository.crear_animal(db, {
            "codigo_animal": "X-001", "id_taxonomia": crear_taxonomia_db().id_taxonomia, "id_recinto": 999,
        })


def test_animal_consultar(db, crear_animal_db):
    animal = crear_animal_db(codigo_animal="TO-001")
    assert AnimalRepository.obtener_por_id(db, animal.id_animal).codigo_animal == "TO-001"
    assert AnimalRepository.obtener_por_codigo(db, "TO-001").id_animal == animal.id_animal
    assert AnimalRepository.obtener_por_id(db, 999) is None
    assert AnimalRepository.obtener_por_codigo(db, "NO-001") is None


def test_animal_codigo_duplicado_lanza_error(db, crear_animal_db):
    crear_animal_db(codigo_animal="TO-001")
    with pytest.raises(IntegrityError):
        crear_animal_db(codigo_animal="TO-001")


def test_animal_codigos_con_prefijo_no_mezcla_prefijos_parecidos(db, crear_animal_db):
    crear_animal_db(codigo_animal="CL-001")
    crear_animal_db(codigo_animal="CL-002")
    crear_animal_db(codigo_animal="CLF-001")
    assert sorted(AnimalRepository.obtener_codigos_con_prefijo(db, "CL")) == ["CL-001", "CL-002"]


def test_animal_actualizar(db, crear_animal_db):
    animal = crear_animal_db()
    animal = AnimalRepository.actualizar_animal(db, animal, {"estado_actual": "liberado", "sexo": "hembra"})
    assert (animal.estado_actual, animal.sexo) == ("liberado", "hembra")


@pytest.fixture
def animales_para_filtrar(crear_taxonomia_db, crear_recinto_db, crear_animal_db):
    oso = crear_taxonomia_db(nombre_comun="Oso de anteojos", especie="Tremarctos ornatus")
    condor = crear_taxonomia_db(nombre_comun="Cóndor andino", especie="Vultur gryphus")
    zona_a = crear_recinto_db(nombre_recinto="Zona A")
    zona_b = crear_recinto_db(nombre_recinto="Zona B")
    crear_animal_db(codigo_animal="TO-001", id_taxonomia=oso.id_taxonomia, id_recinto=zona_a.id_recinto)
    crear_animal_db(
        codigo_animal="TO-002", id_taxonomia=oso.id_taxonomia, id_recinto=zona_b.id_recinto, estado_actual="liberado"
    )
    crear_animal_db(codigo_animal="VG-001", id_taxonomia=condor.id_taxonomia, id_recinto=zona_a.id_recinto)
    return {"oso": oso, "condor": condor, "zona_a": zona_a, "zona_b": zona_b}


def _codigos(animales):
    return [a.codigo_animal for a in animales]


def test_animal_listar_sin_filtros_ordenado_por_codigo(db, animales_para_filtrar):
    assert _codigos(AnimalRepository.obtener_todos(db)) == ["TO-001", "TO-002", "VG-001"]


def test_animal_filtrar_por_texto_en_codigo_o_nombre_comun(db, animales_para_filtrar):
    assert _codigos(AnimalRepository.obtener_todos(db, buscar="cóndor")) == ["VG-001"]
    assert _codigos(AnimalRepository.obtener_todos(db, buscar="to-00")) == ["TO-001", "TO-002"]


def test_animal_filtrar_por_especie_estado_y_recinto(db, animales_para_filtrar):
    datos = animales_para_filtrar
    assert _codigos(AnimalRepository.obtener_todos(db, id_taxonomia=datos["oso"].id_taxonomia)) == ["TO-001", "TO-002"]
    assert _codigos(AnimalRepository.obtener_todos(db, estado="liberado")) == ["TO-002"]
    assert _codigos(AnimalRepository.obtener_todos(db, id_recinto=datos["zona_a"].id_recinto)) == ["TO-001", "VG-001"]


def test_animal_filtros_combinados(db, animales_para_filtrar):
    datos = animales_para_filtrar
    resultado = AnimalRepository.obtener_todos(
        db, id_taxonomia=datos["oso"].id_taxonomia, id_recinto=datos["zona_a"].id_recinto, estado="en_centro"
    )
    assert _codigos(resultado) == ["TO-001"]


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
    oso = crear_animal_db()
    condor = crear_animal_db()
    primero = crear_diagnostico_db(oso.id_animal, diagnostico="Primero")
    segundo = crear_diagnostico_db(oso.id_animal, diagnostico="Segundo")
    crear_diagnostico_db(condor.id_animal, diagnostico="De otro animal")

    ids = [d.id_diagnostico for d in DiagnosticoRepository.obtener_por_animal(db, oso.id_animal)]
    # Los más recientes primero
    assert ids == [segundo.id_diagnostico, primero.id_diagnostico]


def test_diagnostico_actualizar(db, crear_animal_db, crear_diagnostico_db):
    diagnostico = crear_diagnostico_db(crear_animal_db().id_animal)
    diagnostico = DiagnosticoRepository.actualizar_diagnostico(db, diagnostico, {"es_critico": True})
    assert diagnostico.es_critico is True


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
