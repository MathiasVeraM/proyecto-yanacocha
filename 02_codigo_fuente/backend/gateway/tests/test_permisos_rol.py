"""Pruebas de los permisos por rol dentro de cada módulo (src/permisos_rol.py)."""
import pytest

from src.modulos import MODULO_FICHAS_EJEMPLARES, MODULO_PLANIFICACION
from src.permisos_rol import (
    ID_ROL_ADMIN,
    ID_ROL_MANEJO_ANIMAL,
    ID_ROL_VETERINARIA,
    ID_ROL_VOLUNTARIO,
    rol_autorizado,
)

TODOS_LOS_ROLES = [ID_ROL_ADMIN, ID_ROL_VETERINARIA, ID_ROL_MANEJO_ANIMAL, ID_ROL_VOLUNTARIO]

ESCRITURAS_VETERINARIA = [
    ("POST", "/api/animales/5/diagnosticos"),
    ("PUT", "/api/animales/diagnosticos/3"),
    ("POST", "/api/animales/diagnosticos/3/tratamientos"),
    ("PUT", "/api/animales/tratamientos/4"),
    ("POST", "/api/animales/tratamientos/4/generar-actividades"),
]

ESCRITURAS_SOLO_MANEJO = [
    ("POST", "/api/actividades"),
    ("POST", "/api/actividades/repetidas"),
    ("PUT", "/api/actividades/7"),
    ("DELETE", "/api/actividades/7"),
    ("POST", "/api/actividades/7/reabrir"),
    ("POST", "/api/actividades/enriquecimientos"),
    ("POST", "/api/actividades/entrenamientos"),
    ("POST", "/api/actividades/limpiezas"),
    ("POST", "/api/actividades/alimentaciones"),
    ("POST", "/api/actividades/dietas"),
    ("PATCH", "/api/actividades/dietas/2"),
    ("POST", "/api/actividades/dietas/2/finalizar"),
    ("POST", "/api/actividades/tomas/generar"),
]

ESCRITURAS_MANEJO_Y_VOLUNTARIOS = [
    ("POST", "/api/actividades/7/completar"),
    ("PATCH", "/api/actividades/7/completar"),
    ("POST", "/api/actividades/7/observaciones"),
]

LECTURAS = [
    ("GET", "/api/actividades"),
    ("GET", "/api/actividades/calendario"),
    ("GET", "/api/actividades/7/observaciones"),
    ("GET", "/api/animales/5/diagnosticos"),
    ("GET", "/api/animales/5/tratamientos"),
    ("GET", "/api/animales/metricas/animales-con-tratamiento-en-curso"),
]


# ---- Reglas (sin pasar por la app) ----

@pytest.mark.parametrize("metodo,ruta", ESCRITURAS_VETERINARIA)
@pytest.mark.parametrize("id_rol", TODOS_LOS_ROLES)
def test_diagnosticos_y_tratamientos_solo_los_escribe_veterinaria(metodo, ruta, id_rol):
    assert rol_autorizado(metodo, ruta, id_rol) is (id_rol == ID_ROL_VETERINARIA)


@pytest.mark.parametrize("metodo,ruta", ESCRITURAS_SOLO_MANEJO)
@pytest.mark.parametrize("id_rol", TODOS_LOS_ROLES)
def test_crear_editar_eliminar_actividades_y_dietas_solo_manejo(metodo, ruta, id_rol):
    assert rol_autorizado(metodo, ruta, id_rol) is (id_rol == ID_ROL_MANEJO_ANIMAL)


@pytest.mark.parametrize("metodo,ruta", ESCRITURAS_MANEJO_Y_VOLUNTARIOS)
@pytest.mark.parametrize("id_rol", TODOS_LOS_ROLES)
def test_completar_y_observar_lo_hacen_manejo_y_voluntarios(metodo, ruta, id_rol):
    esperado = id_rol in {ID_ROL_MANEJO_ANIMAL, ID_ROL_VOLUNTARIO}
    assert rol_autorizado(metodo, ruta, id_rol) is esperado


@pytest.mark.parametrize("ruta", ["/api/actividades/tomas/renovar", "/api/actividades/tratamientos/renovar"])
@pytest.mark.parametrize("id_rol", TODOS_LOS_ROLES)
def test_la_renovacion_del_horizonte_la_dispara_cualquier_rol(ruta, id_rol):
    # Se ejecuta al abrir Planificación, sin importar quién la abra
    assert rol_autorizado("POST", ruta, id_rol)


@pytest.mark.parametrize("id_rol", TODOS_LOS_ROLES)
def test_generar_dosis_de_un_tratamiento(id_rol):
    esperado = id_rol in {ID_ROL_VETERINARIA, ID_ROL_MANEJO_ANIMAL}
    assert rol_autorizado("POST", "/api/actividades/tratamientos/4/generar", id_rol) is esperado


@pytest.mark.parametrize("metodo,ruta", LECTURAS)
@pytest.mark.parametrize("id_rol", TODOS_LOS_ROLES)
def test_las_lecturas_no_se_restringen_por_rol(metodo, ruta, id_rol):
    assert rol_autorizado(metodo, ruta, id_rol)


@pytest.mark.parametrize(
    "metodo,ruta",
    [
        ("POST", "/api/animales/recintos"),
        ("POST", "/api/animales/taxonomia"),
        ("POST", "/api/auth/usuarios"),
    ],
)
def test_rutas_sin_regla_no_cambian(metodo, ruta):
    assert rol_autorizado(metodo, ruta, ID_ROL_ADMIN)


def test_barra_final_no_evita_la_regla():
    assert not rol_autorizado("POST", "/api/actividades/", ID_ROL_VOLUNTARIO)
    assert not rol_autorizado("POST", "/api/animales/5/diagnosticos/", ID_ROL_MANEJO_ANIMAL)


def test_metodo_en_minusculas():
    assert not rol_autorizado("delete", "/api/actividades/7", ID_ROL_VOLUNTARIO)


@pytest.mark.parametrize("id_rol", [None, "3", 99, [3], {"id": 3}])
def test_rol_desconocido_no_puede_escribir_en_rutas_restringidas(id_rol):
    assert not rol_autorizado("POST", "/api/actividades", id_rol)
    assert not rol_autorizado("POST", "/api/animales/5/diagnosticos", id_rol)


ESCRITURAS_FICHA = [
    ("POST", "/api/animales"),
    ("PUT", "/api/animales/5"),
    ("PUT", "/api/animales/5/imagen"),
]


@pytest.mark.parametrize("metodo,ruta", ESCRITURAS_FICHA)
@pytest.mark.parametrize("id_rol", TODOS_LOS_ROLES)
def test_registrar_editar_y_dar_salida_solo_veterinaria_y_manejo(metodo, ruta, id_rol):
    esperado = id_rol in {ID_ROL_VETERINARIA, ID_ROL_MANEJO_ANIMAL}
    assert rol_autorizado(metodo, ruta, id_rol) is esperado


def test_administrador_no_registra_ni_edita_fichas(client_anonimo, servicio, headers_admin):
    assert client_anonimo.get("/api/animales", headers=headers_admin).status_code == 200
    assert client_anonimo.post("/api/animales", headers=headers_admin, json={}).status_code == 403
    assert client_anonimo.put("/api/animales/5", headers=headers_admin, json={}).status_code == 403
    assert len(servicio.peticiones) == 1


def test_manejo_de_animales_registra_fichas(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(id_rol=ID_ROL_MANEJO_ANIMAL, modulos=[MODULO_FICHAS_EJEMPLARES])

    response = client_anonimo.post("/api/animales", headers=cabeceras(token), json={})

    assert response.status_code == 200
    assert len(servicio.peticiones) == 1


# ---- Integración con el gateway ----

def test_voluntario_no_crea_actividades_y_no_llega_al_servicio(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(id_rol=ID_ROL_VOLUNTARIO, modulos=[MODULO_PLANIFICACION])

    response = client_anonimo.post("/api/actividades", headers=cabeceras(token), json={})

    assert response.status_code == 403
    assert response.json() == {"detail": "Tu rol no tiene permiso para realizar esta acción"}
    assert servicio.peticiones == []


def test_voluntario_completa_actividades(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(id_rol=ID_ROL_VOLUNTARIO, modulos=[MODULO_PLANIFICACION])

    response = client_anonimo.post("/api/actividades/7/completar", headers=cabeceras(token), json={})

    assert response.status_code == 200
    assert len(servicio.peticiones) == 1


def test_administrador_solo_consulta_planificacion(client_anonimo, servicio, headers_admin):
    assert client_anonimo.get("/api/actividades", headers=headers_admin).status_code == 200
    assert client_anonimo.post("/api/actividades/7/completar", headers=headers_admin).status_code == 403
    assert len(servicio.peticiones) == 1


def test_administrador_no_registra_diagnosticos(client_anonimo, servicio, headers_admin):
    assert client_anonimo.get("/api/animales/5/diagnosticos", headers=headers_admin).status_code == 200
    assert client_anonimo.post("/api/animales/5/diagnosticos", headers=headers_admin).status_code == 403
    assert len(servicio.peticiones) == 1


def test_veterinaria_registra_diagnosticos(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(id_rol=ID_ROL_VETERINARIA, modulos=[MODULO_FICHAS_EJEMPLARES])

    response = client_anonimo.post("/api/animales/5/diagnosticos", headers=cabeceras(token), json={})

    assert response.status_code == 200
    assert len(servicio.peticiones) == 1


def test_veterinaria_no_modifica_planificacion(client_anonimo, servicio, crear_token, cabeceras):
    token = crear_token(id_rol=ID_ROL_VETERINARIA, modulos=[MODULO_PLANIFICACION])

    assert client_anonimo.get("/api/actividades/calendario", headers=cabeceras(token)).status_code == 200
    assert client_anonimo.post("/api/actividades/7/observaciones", headers=cabeceras(token)).status_code == 403
    assert len(servicio.peticiones) == 1


def test_el_permiso_de_modulo_se_revisa_antes_que_el_rol(client_anonimo, servicio, crear_token, cabeceras):
    # Manejo de Animales sin el módulo de planificación: 403 por módulo, no por rol
    token = crear_token(id_rol=ID_ROL_MANEJO_ANIMAL, modulos=[MODULO_FICHAS_EJEMPLARES])

    response = client_anonimo.post("/api/actividades", headers=cabeceras(token))

    assert response.status_code == 403
    assert response.json() == {"detail": "No tienes permiso para acceder a este módulo"}
    assert servicio.peticiones == []
