from datetime import timedelta

import pytest

from src.modelos.animal_model import hoy_local

URL = "/api/animales"
NUEVO_ANIMAL = {"codigo_animal": "YNC-100", "nombre_comun": "Oso de anteojos", "especie": "Tremarctos ornatus"}


@pytest.fixture
def h(headers_con_permiso):
    return headers_con_permiso


def _crear_animal(client, h, **datos):
    resp = client.post(URL, json={**NUEVO_ANIMAL, **datos}, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()


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
    ("POST", URL, NUEVO_ANIMAL),
    ("GET", f"{URL}/1", None),
    ("PUT", f"{URL}/1", {"nombre_comun": "X"}),
    ("DELETE", f"{URL}/1", None),
    ("GET", f"{URL}/1/diagnosticos", None),
    ("POST", f"{URL}/1/diagnosticos", {"diagnostico": "X"}),
    ("PUT", f"{URL}/diagnosticos/1", {"diagnostico": "X"}),
    ("GET", f"{URL}/diagnosticos/1/tratamientos", None),
    ("POST", f"{URL}/diagnosticos/1/tratamientos", {"medicamento_o_proceso": "X"}),
    ("PUT", f"{URL}/tratamientos/1", {"estado": "finalizado"}),
]


@pytest.mark.parametrize("metodo,url,cuerpo", ENDPOINTS)
def test_todas_las_rutas_sin_token_401(client, metodo, url, cuerpo):
    assert client.request(metodo, url, json=cuerpo).status_code == 401


@pytest.mark.parametrize("metodo,url,cuerpo", ENDPOINTS)
def test_todas_las_rutas_sin_permiso_403(client, headers_sin_permiso, metodo, url, cuerpo):
    assert client.request(metodo, url, json=cuerpo, headers=headers_sin_permiso).status_code == 403


# ---------- Animales ----------

def test_crear_animal_con_valores_por_defecto(client, h):
    animal = _crear_animal(client, h)
    assert animal["codigo_animal"] == "YNC-100"
    assert animal["estado_actual"] == "en_centro"
    assert animal["fecha_ingreso"] == hoy_local().isoformat()
    assert animal["sexo"] is None


def test_crear_animal_limpia_espacios(client, h):
    animal = _crear_animal(client, h, codigo_animal="  YNC-200  ", nombre_comun=" Cóndor ")
    assert (animal["codigo_animal"], animal["nombre_comun"]) == ("YNC-200", "Cóndor")


def test_crear_animal_codigo_duplicado_400(client, h):
    _crear_animal(client, h)
    resp = client.post(URL, json=NUEVO_ANIMAL, headers=h)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Ya existe un animal con ese código"


@pytest.mark.parametrize("cambio", [
    {"codigo_animal": ""},
    {"nombre_comun": "   "},
    {"sexo": "otro"},
    {"estado_actual": "perdido"},
    {"fecha_ingreso": "no-es-fecha"},
])
def test_crear_animal_datos_invalidos_422(client, h, cambio):
    assert client.post(URL, json={**NUEVO_ANIMAL, **cambio}, headers=h).status_code == 422


def test_crear_animal_sin_campos_obligatorios_422(client, h):
    assert client.post(URL, json={"especie": "X"}, headers=h).status_code == 422


def test_listar_y_obtener_animal(client, h):
    creado = _crear_animal(client, h)
    _crear_animal(client, h, codigo_animal="YNC-050")
    lista = client.get(URL, headers=h).json()
    assert [a["codigo_animal"] for a in lista] == ["YNC-050", "YNC-100"]

    resp = client.get(f"{URL}/{creado['id_animal']}", headers=h)
    assert resp.status_code == 200 and resp.json()["nombre_comun"] == "Oso de anteojos"


def test_obtener_animal_inexistente_404(client, h):
    resp = client.get(f"{URL}/999", headers=h)
    assert resp.status_code == 404 and resp.json()["detail"] == "Animal no encontrado"


def test_actualizar_animal(client, h):
    animal = _crear_animal(client, h, sexo="hembra")
    resp = client.put(
        f"{URL}/{animal['id_animal']}",
        json={"estado_actual": "liberado", "sexo": None, "especie": "Otra"},
        headers=h,
    )
    assert resp.status_code == 200
    datos = resp.json()
    # Los opcionales se pueden vaciar; lo no enviado se conserva
    assert (datos["estado_actual"], datos["sexo"], datos["especie"]) == ("liberado", None, "Otra")
    assert datos["nombre_comun"] == "Oso de anteojos"


def test_actualizar_animal_ignora_null_en_obligatorios(client, h):
    animal = _crear_animal(client, h)
    resp = client.put(f"{URL}/{animal['id_animal']}", json={"nombre_comun": None}, headers=h)
    assert resp.status_code == 200 and resp.json()["nombre_comun"] == "Oso de anteojos"


def test_actualizar_animal_mismo_codigo_200(client, h):
    animal = _crear_animal(client, h)
    resp = client.put(f"{URL}/{animal['id_animal']}", json={"codigo_animal": "YNC-100"}, headers=h)
    assert resp.status_code == 200


def test_actualizar_animal_codigo_de_otro_400(client, h):
    _crear_animal(client, h, codigo_animal="YNC-001")
    animal = _crear_animal(client, h, codigo_animal="YNC-002")
    resp = client.put(f"{URL}/{animal['id_animal']}", json={"codigo_animal": "YNC-001"}, headers=h)
    assert resp.status_code == 400


def test_actualizar_animal_inexistente_404(client, h):
    assert client.put(f"{URL}/999", json={"nombre_comun": "X"}, headers=h).status_code == 404


def test_eliminar_animal_sin_historial_204(client, h):
    animal = _crear_animal(client, h)
    assert client.delete(f"{URL}/{animal['id_animal']}", headers=h).status_code == 204
    assert client.get(f"{URL}/{animal['id_animal']}", headers=h).status_code == 404


def test_eliminar_animal_con_diagnosticos_409(client, h):
    animal = _crear_animal(client, h)
    _crear_diagnostico(client, h, animal["id_animal"])
    resp = client.delete(f"{URL}/{animal['id_animal']}", headers=h)
    assert resp.status_code == 409
    assert client.get(f"{URL}/{animal['id_animal']}", headers=h).status_code == 200


def test_eliminar_animal_inexistente_404(client, h):
    assert client.delete(f"{URL}/999", headers=h).status_code == 404


# ---------- Diagnósticos ----------

def test_crear_diagnostico_usa_el_usuario_del_token(client, h, id_veterinario):
    animal = _crear_animal(client, h)
    # Aunque el cliente envíe otro id_usuario, se ignora y se usa el del token
    diagnostico = _crear_diagnostico(client, h, animal["id_animal"], id_usuario=12345, es_critico=True)
    assert diagnostico["id_usuario"] == id_veterinario
    assert diagnostico["id_animal"] == animal["id_animal"]
    assert diagnostico["es_critico"] is True


def test_crear_diagnostico_animal_inexistente_404(client, h):
    resp = client.post(f"{URL}/999/diagnosticos", json={"diagnostico": "X"}, headers=h)
    assert resp.status_code == 404


def test_crear_diagnostico_vacio_422(client, h):
    animal = _crear_animal(client, h)
    resp = client.post(f"{URL}/{animal['id_animal']}/diagnosticos", json={"diagnostico": "  "}, headers=h)
    assert resp.status_code == 422


def test_listar_diagnosticos_del_animal(client, h):
    animal = _crear_animal(client, h)
    otro = _crear_animal(client, h, codigo_animal="YNC-999")
    _crear_diagnostico(client, h, animal["id_animal"], diagnostico="Primero")
    _crear_diagnostico(client, h, animal["id_animal"], diagnostico="Segundo")
    _crear_diagnostico(client, h, otro["id_animal"], diagnostico="Ajeno")

    lista = client.get(f"{URL}/{animal['id_animal']}/diagnosticos", headers=h).json()
    assert [d["diagnostico"] for d in lista] == ["Segundo", "Primero"]


def test_listar_diagnosticos_animal_inexistente_404(client, h):
    assert client.get(f"{URL}/999/diagnosticos", headers=h).status_code == 404


def test_actualizar_diagnostico(client, h):
    animal = _crear_animal(client, h)
    diagnostico = _crear_diagnostico(client, h, animal["id_animal"])
    resp = client.put(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}",
        json={"observaciones": "Mejora notable", "es_critico": True},
        headers=h,
    )
    assert resp.status_code == 200
    assert (resp.json()["observaciones"], resp.json()["es_critico"]) == ("Mejora notable", True)
    assert resp.json()["diagnostico"] == "Deshidratación leve"


def test_actualizar_diagnostico_no_cambia_animal_ni_usuario(client, h, id_veterinario):
    animal = _crear_animal(client, h)
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

def _diagnostico_listo(client, h):
    animal = _crear_animal(client, h)
    return _crear_diagnostico(client, h, animal["id_animal"])


def test_crear_tratamiento_con_valores_por_defecto(client, h):
    diagnostico = _diagnostico_listo(client, h)
    tratamiento = _crear_tratamiento(client, h, diagnostico["id_diagnostico"], dosis="50 ml")
    assert tratamiento["estado"] == "en_curso"
    assert tratamiento["fecha_inicio"] == hoy_local().isoformat()
    assert tratamiento["fecha_fin"] is None
    assert tratamiento["dosis"] == "50 ml"


def test_crear_tratamiento_diagnostico_inexistente_404(client, h):
    resp = client.post(f"{URL}/diagnosticos/999/tratamientos", json={"medicamento_o_proceso": "X"}, headers=h)
    assert resp.status_code == 404


def test_crear_tratamiento_fecha_fin_anterior_400(client, h):
    diagnostico = _diagnostico_listo(client, h)
    hoy = hoy_local()
    resp = client.post(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}/tratamientos",
        json={"medicamento_o_proceso": "X", "fecha_inicio": hoy.isoformat(),
              "fecha_fin": (hoy - timedelta(days=1)).isoformat()},
        headers=h,
    )
    assert resp.status_code == 400


def test_crear_tratamiento_fecha_fin_antes_de_hoy_sin_inicio_400(client, h):
    # Sin fecha_inicio se toma hoy, así que un fin en el pasado no es válido
    diagnostico = _diagnostico_listo(client, h)
    ayer = (hoy_local() - timedelta(days=1)).isoformat()
    resp = client.post(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}/tratamientos",
        json={"medicamento_o_proceso": "X", "fecha_fin": ayer},
        headers=h,
    )
    assert resp.status_code == 400


def test_crear_tratamiento_estado_invalido_422(client, h):
    diagnostico = _diagnostico_listo(client, h)
    resp = client.post(
        f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}/tratamientos",
        json={"medicamento_o_proceso": "X", "estado": "olvidado"},
        headers=h,
    )
    assert resp.status_code == 422


def test_listar_tratamientos(client, h):
    diagnostico = _diagnostico_listo(client, h)
    _crear_tratamiento(client, h, diagnostico["id_diagnostico"], medicamento_o_proceso="Antibiótico")
    resp = client.get(f"{URL}/diagnosticos/{diagnostico['id_diagnostico']}/tratamientos", headers=h)
    assert [t["medicamento_o_proceso"] for t in resp.json()] == ["Antibiótico"]


def test_listar_tratamientos_diagnostico_inexistente_404(client, h):
    assert client.get(f"{URL}/diagnosticos/999/tratamientos", headers=h).status_code == 404


def test_finalizar_tratamiento(client, h):
    diagnostico = _diagnostico_listo(client, h)
    tratamiento = _crear_tratamiento(client, h, diagnostico["id_diagnostico"])
    hoy = hoy_local().isoformat()
    resp = client.put(
        f"{URL}/tratamientos/{tratamiento['id_tratamiento']}",
        json={"estado": "finalizado", "fecha_fin": hoy},
        headers=h,
    )
    assert resp.status_code == 200
    assert (resp.json()["estado"], resp.json()["fecha_fin"]) == ("finalizado", hoy)


def test_actualizar_tratamiento_fecha_fin_anterior_a_la_guardada_400(client, h):
    # Solo se envía fecha_fin: se compara contra la fecha_inicio ya guardada
    diagnostico = _diagnostico_listo(client, h)
    tratamiento = _crear_tratamiento(client, h, diagnostico["id_diagnostico"])
    ayer = (hoy_local() - timedelta(days=1)).isoformat()
    resp = client.put(f"{URL}/tratamientos/{tratamiento['id_tratamiento']}", json={"fecha_fin": ayer}, headers=h)
    assert resp.status_code == 400


def test_actualizar_tratamiento_inexistente_404(client, h):
    assert client.put(f"{URL}/tratamientos/999", json={"estado": "finalizado"}, headers=h).status_code == 404
