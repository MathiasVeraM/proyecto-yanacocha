from datetime import timedelta

import pytest

from src.modelos.fechas import hoy_local

URL = "/api/animales"


@pytest.fixture
def h(headers_con_permiso):
    return headers_con_permiso


@pytest.fixture
def oso(crear_taxonomia_db):
    return crear_taxonomia_db(nombre_comun="Oso de anteojos", especie="Tremarctos ornatus")


@pytest.fixture
def recinto(crear_recinto_db):
    return crear_recinto_db(nombre_recinto="Sector de osos")


@pytest.fixture
def nuevo_animal(oso, recinto):
    return {"id_taxonomia": oso.id_taxonomia, "id_recinto": recinto.id_recinto}


@pytest.fixture
def crear_animal(client, h, nuevo_animal):
    def _crear(**datos):
        resp = client.post(URL, json={**nuevo_animal, **datos}, headers=h)
        assert resp.status_code == 201, resp.text
        return resp.json()
    return _crear


def _crear_diagnostico(client, h, id_animal, **datos):
    cuerpo = {"diagnostico": "Deshidratación leve", **datos}
    resp = client.post(f"{URL}/{id_animal}/diagnosticos", json=cuerpo, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _crear_tratamiento(client, h, id_diagnostico, **datos):
    cuerpo = {"medicamento_o_proceso": "Suero oral", **datos}
    resp = client.post(f"{URL}/diagnosticos/{id_diagnostico}/tratamientos", json=cuerpo, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()


# Todas las rutas del servicio deben exigir permiso sobre el módulo
ENDPOINTS = [
    ("GET", URL, None),
    ("POST", URL, {"id_taxonomia": 1, "id_recinto": 1}),
    ("GET", f"{URL}/1", None),
    ("PUT", f"{URL}/1", {"sexo": "macho"}),
    ("GET", f"{URL}/1/diagnosticos", None),
    ("POST", f"{URL}/1/diagnosticos", {"diagnostico": "X"}),
    ("PUT", f"{URL}/diagnosticos/1", {"diagnostico": "X"}),
    ("GET", f"{URL}/1/signos-vitales", None),
    ("GET", f"{URL}/diagnosticos/1/tratamientos", None),
    ("POST", f"{URL}/diagnosticos/1/tratamientos", {"medicamento_o_proceso": "X"}),
    ("PUT", f"{URL}/tratamientos/1", {"estado": "finalizado"}),
    ("GET", f"{URL}/taxonomia", None),
    ("GET", f"{URL}/taxonomia/sugerencias?buscar=oso", None),
    ("POST", f"{URL}/taxonomia", {"nombre_comun": "X", "especie": "X y"}),
    ("POST", f"{URL}/taxonomia/importar", {"id_inaturalist": 1}),
    ("PUT", f"{URL}/taxonomia/1", {"familia": "X"}),
    ("GET", f"{URL}/recintos", None),
    ("POST", f"{URL}/recintos", {"nombre_recinto": "X"}),
    ("PUT", f"{URL}/recintos/1", {"estado": "en_limpieza"}),
]


@pytest.mark.parametrize("metodo,url,cuerpo", ENDPOINTS)
def test_todas_las_rutas_sin_token_401(client, metodo, url, cuerpo):
    assert client.request(metodo, url, json=cuerpo).status_code == 401


@pytest.mark.parametrize("metodo,url,cuerpo", ENDPOINTS)
def test_todas_las_rutas_sin_permiso_403(client, headers_sin_permiso, metodo, url, cuerpo):
    assert client.request(metodo, url, json=cuerpo, headers=headers_sin_permiso).status_code == 403


# ---------- Animales: registro y código automático ----------

def test_crear_animal_genera_codigo_y_valores_por_defecto(crear_animal):
    animal = crear_animal()
    assert animal["codigo_animal"] == "TO-001"
    assert animal["estado_actual"] == "en_centro"
    assert animal["fecha_ingreso"] == hoy_local().isoformat()
    # La ficha incluye la taxonomía y el recinto completos
    assert animal["taxonomia"]["especie"] == "Tremarctos ornatus"
    assert animal["taxonomia"]["nombre_comun"] == "Oso de anteojos"
    assert animal["recinto"]["nombre_recinto"] == "Sector de osos"


def test_codigo_aumenta_por_especie(crear_animal, crear_taxonomia_db):
    perro = crear_taxonomia_db(nombre_comun="Perro", especie="Canis lupus familiaris")
    assert crear_animal()["codigo_animal"] == "TO-001"
    assert crear_animal(id_taxonomia=perro.id_taxonomia)["codigo_animal"] == "CLF-001"
    assert crear_animal(id_taxonomia=perro.id_taxonomia)["codigo_animal"] == "CLF-002"
    assert crear_animal()["codigo_animal"] == "TO-002"


def test_especies_con_mismas_iniciales_comparten_contador(crear_animal, crear_taxonomia_db):
    lobo = crear_taxonomia_db(nombre_comun="Lobo", especie="Canis lupus")
    capuchino = crear_taxonomia_db(nombre_comun="Capuchino", especie="Cebus libidinosus")
    assert crear_animal(id_taxonomia=lobo.id_taxonomia)["codigo_animal"] == "CL-001"
    assert crear_animal(id_taxonomia=capuchino.id_taxonomia)["codigo_animal"] == "CL-002"


def test_el_codigo_enviado_por_el_cliente_se_ignora(crear_animal):
    assert crear_animal(codigo_animal="MIO-999")["codigo_animal"] == "TO-001"


def test_si_el_codigo_se_ocupa_a_la_vez_reintenta_con_el_siguiente(crear_animal, monkeypatch):
    # Simula que otro registro tomó TO-001 justo antes: la primera consulta no lo ve
    from src.repositorios.animal_repo import AnimalRepository
    crear_animal()
    original = AnimalRepository.obtener_codigos_con_prefijo
    llamadas = []

    def _desactualizado(db, prefijo):
        llamadas.append(prefijo)
        return [] if len(llamadas) == 1 else original(db, prefijo)

    monkeypatch.setattr(AnimalRepository, "obtener_codigos_con_prefijo", staticmethod(_desactualizado))
    assert crear_animal()["codigo_animal"] == "TO-002"
    assert len(llamadas) == 2


def test_si_no_logra_un_codigo_libre_responde_409(client, h, nuevo_animal, crear_animal, monkeypatch):
    from src.repositorios.animal_repo import AnimalRepository
    crear_animal()
    monkeypatch.setattr(AnimalRepository, "obtener_codigos_con_prefijo", staticmethod(lambda db, prefijo: []))
    assert client.post(URL, json=nuevo_animal, headers=h).status_code == 409


def test_crear_animal_especie_inexistente_400(client, h, recinto):
    resp = client.post(URL, json={"id_taxonomia": 999, "id_recinto": recinto.id_recinto}, headers=h)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "La especie indicada no existe en el catálogo"


def test_crear_animal_recinto_inexistente_400(client, h, oso):
    resp = client.post(URL, json={"id_taxonomia": oso.id_taxonomia, "id_recinto": 999}, headers=h)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "El recinto indicado no existe"


@pytest.mark.parametrize("faltante", ["id_taxonomia", "id_recinto"])
def test_crear_animal_sin_especie_o_recinto_422(client, h, nuevo_animal, faltante):
    cuerpo = {k: v for k, v in nuevo_animal.items() if k != faltante}
    assert client.post(URL, json=cuerpo, headers=h).status_code == 422


@pytest.mark.parametrize("cambio", [
    {"sexo": "otro"},
    {"estado_actual": "perdido"},
    {"fecha_ingreso": "no-es-fecha"},
])
def test_crear_animal_datos_invalidos_422(client, h, nuevo_animal, cambio):
    assert client.post(URL, json={**nuevo_animal, **cambio}, headers=h).status_code == 422


# ---------- Animales: consulta, filtros y edición ----------

def test_obtener_animal(client, h, crear_animal):
    creado = crear_animal()
    resp = client.get(f"{URL}/{creado['id_animal']}", headers=h)
    assert resp.status_code == 200 and resp.json()["codigo_animal"] == "TO-001"


def test_obtener_animal_inexistente_404(client, h):
    resp = client.get(f"{URL}/999", headers=h)
    assert resp.status_code == 404 and resp.json()["detail"] == "Animal no encontrado"


@pytest.fixture
def varios_animales(crear_animal, crear_taxonomia_db, crear_recinto_db):
    condor = crear_taxonomia_db(nombre_comun="Cóndor andino", especie="Vultur gryphus")
    aviario = crear_recinto_db(nombre_recinto="Aviario")
    crear_animal()  # TO-001 en Sector de osos
    crear_animal(estado_actual="liberado")  # TO-002
    crear_animal(id_taxonomia=condor.id_taxonomia, id_recinto=aviario.id_recinto)  # VG-001
    return {"condor": condor, "aviario": aviario}


def _codigos(resp):
    assert resp.status_code == 200, resp.text
    return [a["codigo_animal"] for a in resp.json()]


def test_listar_sin_filtros(client, h, varios_animales):
    assert _codigos(client.get(URL, headers=h)) == ["TO-001", "TO-002", "VG-001"]


def test_listar_filtrando_por_especie(client, h, varios_animales):
    resp = client.get(URL, params={"id_taxonomia": varios_animales["condor"].id_taxonomia}, headers=h)
    assert _codigos(resp) == ["VG-001"]


def test_listar_filtrando_por_estado_recinto_y_texto(client, h, varios_animales):
    assert _codigos(client.get(URL, params={"estado": "liberado"}, headers=h)) == ["TO-002"]
    assert _codigos(client.get(URL, params={"id_recinto": varios_animales["aviario"].id_recinto}, headers=h)) == ["VG-001"]
    assert _codigos(client.get(URL, params={"buscar": "oso"}, headers=h)) == ["TO-001", "TO-002"]


def test_listar_estado_invalido_422(client, h):
    assert client.get(URL, params={"estado": "perdido"}, headers=h).status_code == 422


def test_actualizar_animal(client, h, crear_animal):
    animal = crear_animal(sexo="hembra", edad_aproximada="2 años")
    resp = client.put(
        f"{URL}/{animal['id_animal']}",
        json={"estado_actual": "liberado", "sexo": None},
        headers=h,
    )
    assert resp.status_code == 200
    datos = resp.json()
    # Los opcionales se pueden vaciar; lo no enviado se conserva
    assert (datos["estado_actual"], datos["sexo"], datos["edad_aproximada"]) == ("liberado", None, "2 años")


def test_mover_animal_de_recinto(client, h, crear_animal, crear_recinto_db):
    animal = crear_animal()
    nuevo = crear_recinto_db(nombre_recinto="Cuarentena")
    resp = client.put(f"{URL}/{animal['id_animal']}", json={"id_recinto": nuevo.id_recinto}, headers=h)
    assert resp.status_code == 200
    assert resp.json()["recinto"]["nombre_recinto"] == "Cuarentena"


def test_mover_animal_a_recinto_inexistente_400(client, h, crear_animal):
    animal = crear_animal()
    assert client.put(f"{URL}/{animal['id_animal']}", json={"id_recinto": 999}, headers=h).status_code == 400


def test_actualizar_animal_ignora_null_en_obligatorios(client, h, crear_animal):
    animal = crear_animal()
    resp = client.put(f"{URL}/{animal['id_animal']}", json={"id_recinto": None, "estado_actual": None}, headers=h)
    assert resp.status_code == 200
    assert resp.json()["recinto"]["nombre_recinto"] == "Sector de osos"
    assert resp.json()["estado_actual"] == "en_centro"


def test_codigo_y_especie_no_se_pueden_editar(client, h, crear_animal, crear_taxonomia_db):
    animal = crear_animal()
    perro = crear_taxonomia_db(nombre_comun="Perro", especie="Canis lupus familiaris")
    resp = client.put(
        f"{URL}/{animal['id_animal']}",
        json={"codigo_animal": "OTRO-001", "id_taxonomia": perro.id_taxonomia},
        headers=h,
    )
    assert (resp.json()["codigo_animal"], resp.json()["taxonomia"]["nombre_comun"]) == ("TO-001", "Oso de anteojos")


def test_actualizar_animal_inexistente_404(client, h):
    assert client.put(f"{URL}/999", json={"sexo": "macho"}, headers=h).status_code == 404


def test_no_existe_delete_de_animales(client, h, crear_animal):
    # HU-02: ningún animal se elimina físicamente, por trazabilidad
    animal = crear_animal()
    assert client.delete(f"{URL}/{animal['id_animal']}", headers=h).status_code == 405
    assert client.get(f"{URL}/{animal['id_animal']}", headers=h).status_code == 200


# ---------- Diagnósticos ----------

def test_crear_diagnostico_usa_el_usuario_del_token(client, h, id_veterinario, crear_animal):
    animal = crear_animal()
    # Aunque el cliente envíe otro id_usuario, se ignora y se usa el del token
    diagnostico = _crear_diagnostico(client, h, animal["id_animal"], id_usuario=12345, es_critico=True)
    assert diagnostico["id_usuario"] == id_veterinario
    assert diagnostico["id_animal"] == animal["id_animal"]
    assert diagnostico["es_critico"] is True
    assert diagnostico["signos_vitales"] is None


def test_crear_diagnostico_con_signos_vitales(client, h, crear_animal):
    animal = crear_animal()
    diagnostico = _crear_diagnostico(
        client,
        h,
        animal["id_animal"],
        signos_vitales={
            "peso_kg": 0.125,
            "temperatura_c": 37.5,
            "frecuencia_cardiaca_lpm": 120,
            "frecuencia_respiratoria_rpm": 24,
            "tiempo_llenado_capilar_s": 1.5,
            "hidratacion": "deshidratacion_leve",
            "condicion_corporal": 3,
            "mucosas": "rosadas",
            "actitud": "alerta",
        },
    )
    signos = diagnostico["signos_vitales"]
    assert signos["id_signos_vitales"] > 0
    assert signos["id_diagnostico"] == diagnostico["id_diagnostico"]
    assert signos["peso_kg"] == 0.125
    assert signos["temperatura_c"] == 37.5
    assert signos["hidratacion"] == "deshidratacion_leve"


@pytest.mark.parametrize(
    "signos",
    [
        {},
        {"peso_kg": 0},
        {"peso_kg": 0.0001},
        {"frecuencia_cardiaca_lpm": 0},
        {"frecuencia_respiratoria_rpm": -1},
        {"tiempo_llenado_capilar_s": 0},
        {"temperatura_c": 60.1},
        {"temperatura_c": 36.55},
        {"hidratacion": "critica"},
        {"condicion_corporal": 6},
        {"mucosas": "verdes"},
        {"actitud": "inconsciente"},
    ],
)
def test_signos_vitales_invalidos_rechazados(client, h, crear_animal, signos):
    animal = crear_animal()
    resp = client.post(
        f"{URL}/{animal['id_animal']}/diagnosticos",
        json={"diagnostico": "Control clínico", "signos_vitales": signos},
        headers=h,
    )
    assert resp.status_code == 422


def test_listar_historial_signos_vitales_ordenado_por_fecha(client, h, crear_animal):
    animal = crear_animal()
    anterior = _crear_diagnostico(
        client,
        h,
        animal["id_animal"],
        diagnostico="Control anterior",
        signos_vitales={"peso_kg": 2.5},
    )
    reciente = _crear_diagnostico(
        client,
        h,
        animal["id_animal"],
        diagnostico="Control reciente",
        signos_vitales={"temperatura_c": 38.2},
    )

    resp = client.get(f"{URL}/{animal['id_animal']}/signos-vitales", headers=h)
    assert resp.status_code == 200
    historial = resp.json()
    assert [s["id_diagnostico"] for s in historial] == [
        reciente["id_diagnostico"],
        anterior["id_diagnostico"],
    ]
    assert all(s["fecha_diagnostico"] for s in historial)


def test_historial_signos_vitales_animal_inexistente_404(client, h):
    assert client.get(f"{URL}/999/signos-vitales", headers=h).status_code == 404


def test_signos_vitales_no_exigen_rango_normal_por_especie(client, h, crear_animal):
    animal = crear_animal()
    diagnostico = _crear_diagnostico(
        client,
        h,
        animal["id_animal"],
        signos_vitales={"peso_kg": 0.001, "temperatura_c": 0, "frecuencia_cardiaca_lpm": 1},
    )
    assert diagnostico["signos_vitales"]["temperatura_c"] == 0


def test_crear_diagnostico_animal_inexistente_404(client, h):
    resp = client.post(f"{URL}/999/diagnosticos", json={"diagnostico": "X"}, headers=h)
    assert resp.status_code == 404


def test_crear_diagnostico_vacio_422(client, h, crear_animal):
    animal = crear_animal()
    resp = client.post(f"{URL}/{animal['id_animal']}/diagnosticos", json={"diagnostico": "  "}, headers=h)
    assert resp.status_code == 422


def test_listar_diagnosticos_del_animal(client, h, crear_animal):
    animal = crear_animal()
    otro = crear_animal()
    _crear_diagnostico(client, h, animal["id_animal"], diagnostico="Primero")
    _crear_diagnostico(client, h, animal["id_animal"], diagnostico="Segundo")
    _crear_diagnostico(client, h, otro["id_animal"], diagnostico="Ajeno")

    lista = client.get(f"{URL}/{animal['id_animal']}/diagnosticos", headers=h).json()
    assert [d["diagnostico"] for d in lista] == ["Segundo", "Primero"]


def test_listar_diagnosticos_animal_inexistente_404(client, h):
    assert client.get(f"{URL}/999/diagnosticos", headers=h).status_code == 404


def test_actualizar_diagnostico(client, h, crear_animal):
    diagnostico = _crear_diagnostico(client, h, crear_animal()["id_animal"])
    resp = client.put(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}",
        json={"observaciones": "Mejora notable", "es_critico": True},
        headers=h,
    )
    assert resp.status_code == 200
    assert (resp.json()["observaciones"], resp.json()["es_critico"]) == ("Mejora notable", True)
    assert resp.json()["diagnostico"] == "Deshidratación leve"


def test_actualizar_diagnostico_agrega_signos_vitales(client, h, crear_animal):
    diagnostico = _crear_diagnostico(client, h, crear_animal()["id_animal"])
    resp = client.put(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}",
        json={"signos_vitales": {"peso_kg": 0.125, "hidratacion": "normal"}},
        headers=h,
    )
    assert resp.status_code == 200
    assert resp.json()["signos_vitales"]["peso_kg"] == 0.125
    assert resp.json()["signos_vitales"]["hidratacion"] == "normal"


def test_actualizar_diagnostico_edita_signos_vitales(client, h, crear_animal):
    diagnostico = _crear_diagnostico(
        client,
        h,
        crear_animal()["id_animal"],
        signos_vitales={"peso_kg": 1.25, "temperatura_c": 37.5},
    )
    resp = client.put(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}",
        json={"signos_vitales": {"peso_kg": 1.5, "temperatura_c": 38.2}},
        headers=h,
    )
    assert resp.status_code == 200
    assert resp.json()["signos_vitales"]["peso_kg"] == 1.5
    assert resp.json()["signos_vitales"]["temperatura_c"] == 38.2


def test_actualizar_diagnostico_null_elimina_signos_vitales(client, h, crear_animal):
    diagnostico = _crear_diagnostico(
        client,
        h,
        crear_animal()["id_animal"],
        signos_vitales={"peso_kg": 1.25},
    )
    resp = client.put(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}",
        json={"signos_vitales": None},
        headers=h,
    )
    assert resp.status_code == 200
    assert resp.json()["signos_vitales"] is None


def test_actualizar_diagnostico_signos_vitales_invalidos_no_modifica(
    client, h, crear_animal
):
    diagnostico = _crear_diagnostico(
        client,
        h,
        crear_animal()["id_animal"],
        signos_vitales={"peso_kg": 1.25},
    )
    resp = client.put(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}",
        json={"diagnostico": "Texto modificado", "signos_vitales": {"peso_kg": 0}},
        headers=h,
    )
    assert resp.status_code == 422
    actual = client.get(
        f"{URL}/{diagnostico['id_animal']}/diagnosticos",
        headers=h,
    ).json()[0]
    assert actual["diagnostico"] == diagnostico["diagnostico"]
    assert actual["signos_vitales"]["peso_kg"] == 1.25


def test_actualizar_diagnostico_no_cambia_animal_ni_usuario(client, h, id_veterinario, crear_animal):
    animal = crear_animal()
    diagnostico = _crear_diagnostico(client, h, animal["id_animal"])
    resp = client.put(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}",
        json={"id_animal": 999, "id_usuario": 999},
        headers=h,
    )
    assert (resp.json()["id_animal"], resp.json()["id_usuario"]) == (animal["id_animal"], id_veterinario)


def test_actualizar_diagnostico_inexistente_404(client, h):
    assert client.put(f"{URL}/diagnosticos/999", json={"diagnostico": "X"}, headers=h).status_code == 404


# ---------- Tratamientos ----------

@pytest.fixture
def diagnostico(client, h, crear_animal):
    return _crear_diagnostico(client, h, crear_animal()["id_animal"])


def test_crear_tratamiento_con_valores_por_defecto(client, h, diagnostico):
    tratamiento = _crear_tratamiento(client, h, diagnostico["id_diagnostico"], dosis="50 ml")
    assert tratamiento["estado"] == "en_curso"
    assert tratamiento["fecha_inicio"] == hoy_local().isoformat()
    assert tratamiento["fecha_fin"] is None
    assert tratamiento["dosis"] == "50 ml"


def test_crear_tratamiento_diagnostico_inexistente_404(client, h):
    resp = client.post(f"{URL}/diagnosticos/999/tratamientos", json={"medicamento_o_proceso": "X"}, headers=h)
    assert resp.status_code == 404


def test_crear_tratamiento_fecha_fin_anterior_400(client, h, diagnostico):
    hoy = hoy_local()
    resp = client.post(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}/tratamientos",
        json={"medicamento_o_proceso": "X", "fecha_inicio": hoy.isoformat(),
              "fecha_fin": (hoy - timedelta(days=1)).isoformat()},
        headers=h,
    )
    assert resp.status_code == 400


def test_crear_tratamiento_fecha_fin_antes_de_hoy_sin_inicio_400(client, h, diagnostico):
    # Sin fecha_inicio se toma hoy, así que un fin en el pasado no es válido
    ayer = (hoy_local() - timedelta(days=1)).isoformat()
    resp = client.post(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}/tratamientos",
        json={"medicamento_o_proceso": "X", "fecha_fin": ayer},
        headers=h,
    )
    assert resp.status_code == 400


def test_crear_tratamiento_estado_invalido_422(client, h, diagnostico):
    resp = client.post(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}/tratamientos",
        json={"medicamento_o_proceso": "X", "estado": "olvidado"},
        headers=h,
    )
    assert resp.status_code == 422


def test_listar_tratamientos(client, h, diagnostico):
    _crear_tratamiento(client, h, diagnostico["id_diagnostico"], medicamento_o_proceso="Antibiótico")
    resp = client.get(f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}/tratamientos", headers=h)
    assert [t["medicamento_o_proceso"] for t in resp.json()] == ["Antibiótico"]


def test_listar_tratamientos_diagnostico_inexistente_404(client, h):
    assert client.get(f"{URL}/diagnosticos/999/tratamientos", headers=h).status_code == 404


def test_finalizar_tratamiento(client, h, diagnostico):
    tratamiento = _crear_tratamiento(client, h, diagnostico["id_diagnostico"])
    hoy = hoy_local().isoformat()
    resp = client.put(
        f"{URL}/tratamientos/{tratamiento['id_tratamiento']}",
        json={"estado": "finalizado", "fecha_fin": hoy},
        headers=h,
    )
    assert resp.status_code == 200
    assert (resp.json()["estado"], resp.json()["fecha_fin"]) == ("finalizado", hoy)


def test_actualizar_tratamiento_fecha_fin_anterior_a_la_guardada_400(client, h, diagnostico):
    # Solo se envía fecha_fin: se compara contra la fecha_inicio ya guardada
    tratamiento = _crear_tratamiento(client, h, diagnostico["id_diagnostico"])
    ayer = (hoy_local() - timedelta(days=1)).isoformat()
    resp = client.put(f"{URL}/tratamientos/{tratamiento['id_tratamiento']}", json={"fecha_fin": ayer}, headers=h)
    assert resp.status_code == 400


def test_actualizar_tratamiento_inexistente_404(client, h):
    assert client.put(f"{URL}/tratamientos/999", json={"estado": "finalizado"}, headers=h).status_code == 404
