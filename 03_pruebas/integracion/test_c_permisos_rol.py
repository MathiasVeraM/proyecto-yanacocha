"""c) Permisos por rol: quién puede hacer qué (los aplica el gateway y, de nuevo, cada servicio)."""
import pytest

from ayudas import DOMINIO_CORREOS, ROL_MANEJO, ROL_VOLUNTARIO, datos_limpieza, en_dias, exigir, hoy_ec, unico


@pytest.fixture
def limpieza_de_hoy(programar, recinto):
    """Una limpieza programada para hoy (sin hora): es la única que se puede completar sin esperar."""
    return exigir(programar(datos_limpieza(recinto["id_recinto"], hoy_ec())), 201)


# ---------- Solo el administrador gestiona usuarios ----------

@pytest.mark.parametrize("cliente", ["api_veterinaria", "api_manejo", "api_voluntario"])
def test_los_demas_roles_no_gestionan_usuarios(request, cliente):
    api = request.getfixturevalue(cliente)
    datos = {"nombre": "X", "apellido": "Y", "correo": f"{unico('x')}@{DOMINIO_CORREOS}", "password": "clave-larga-123", "id_rol": 4}

    assert api.get("/api/auth/usuarios").status_code == 403
    assert api.post("/api/auth/usuarios", json=datos).status_code == 403
    assert api.put("/api/auth/usuarios/1", json={"nombre": "Otro"}).status_code == 403
    assert api.patch("/api/auth/usuarios/1/desactivar").status_code == 403


def test_el_administrador_crea_edita_y_desactiva_usuarios(api_admin, usuario_temporal):
    usuario = usuario_temporal(ROL_VOLUNTARIO)

    listado = exigir(api_admin.get("/api/auth/usuarios"))
    assert usuario.id_usuario in [u["id_usuario"] for u in listado]

    editado = exigir(api_admin.put(f"/api/auth/usuarios/{usuario.id_usuario}", json={"nombre": "Renombrado", "id_rol": ROL_MANEJO}))
    assert editado["nombre"] == "Renombrado"
    assert editado["id_rol"] == ROL_MANEJO

    desactivado = exigir(api_admin.patch(f"/api/auth/usuarios/{usuario.id_usuario}/desactivar"))
    assert desactivado["activo"] is False


def test_la_respuesta_de_usuarios_no_incluye_la_contrasena(api_admin, usuario_temporal):
    usuario = usuario_temporal()

    listado = exigir(api_admin.get("/api/auth/usuarios"))
    propio = next(u for u in listado if u["id_usuario"] == usuario.id_usuario)

    assert "password" not in propio
    assert "password_hash" not in propio


def test_no_se_repite_un_correo(api_admin, usuario_temporal):
    usuario = usuario_temporal()

    respuesta = api_admin.post(
        "/api/auth/usuarios",
        json={"nombre": "A", "apellido": "B", "correo": usuario.correo, "password": "clave-larga-123", "id_rol": ROL_VOLUNTARIO},
    )

    assert respuesta.status_code == 400


def test_se_valida_el_rol_y_la_longitud_de_la_contrasena(api_admin):
    correo = f"{unico('val')}@{DOMINIO_CORREOS}"
    base = {"nombre": "A", "apellido": "B", "correo": correo}

    assert api_admin.post("/api/auth/usuarios", json={**base, "password": "clave-larga-123", "id_rol": 999}).status_code == 400
    assert api_admin.post("/api/auth/usuarios", json={**base, "password": "corta", "id_rol": ROL_VOLUNTARIO}).status_code == 422


# ---------- Planificación: Manejo de Animales programa; Voluntarios completan ----------

def test_voluntario_no_puede_crear_actividades_403(api_voluntario, recinto):
    respuesta = api_voluntario.post("/api/actividades", json=datos_limpieza(recinto["id_recinto"], en_dias(2), "09:00"))

    assert respuesta.status_code == 403
    assert "rol" in respuesta.json()["detail"]


def test_voluntario_no_puede_editar_eliminar_ni_reabrir(api_voluntario, limpieza_de_hoy):
    ruta = f"/api/actividades/{limpieza_de_hoy['id_actividad']}"

    assert api_voluntario.put(ruta, json={"observaciones": "x"}).status_code == 403
    assert api_voluntario.delete(ruta).status_code == 403
    assert api_voluntario.post(f"{ruta}/reabrir").status_code == 403


def test_voluntario_no_puede_crear_dietas_403(api_voluntario, animal):
    respuesta = api_voluntario.post(
        "/api/actividades/dietas",
        json={
            "id_animal": animal["id_animal"],
            "fecha_inicio": en_dias(1).isoformat(),
            "frecuencia_valor": 1,
            "frecuencia_unidad": "dias",
            "alimentos": [{"nombre_alimento": "Pollo", "cantidad_gramos": 100}],
        },
    )

    assert respuesta.status_code == 403


def test_voluntario_si_puede_completar_actividades(api_voluntario, usuarios, limpieza_de_hoy):
    completada = exigir(
        api_voluntario.post(f"/api/actividades/{limpieza_de_hoy['id_actividad']}/completar", json={"observaciones": "Hecho"})
    )

    assert completada["completada"] is True
    assert completada["id_usuario_completo"] == usuarios["voluntario"].id_usuario
    assert completada["fecha_completada"] is not None


def test_manejo_de_animales_tambien_completa(api_manejo, usuarios, limpieza_de_hoy):
    completada = exigir(api_manejo.post(f"/api/actividades/{limpieza_de_hoy['id_actividad']}/completar", json={}))

    assert completada["id_usuario_completo"] == usuarios["manejo"].id_usuario


def test_veterinaria_no_puede_completar_actividades_403(api_veterinaria, limpieza_de_hoy):
    respuesta = api_veterinaria.post(f"/api/actividades/{limpieza_de_hoy['id_actividad']}/completar", json={})

    assert respuesta.status_code == 403


def test_solo_manejo_de_animales_reabre(api_manejo, api_voluntario, limpieza_de_hoy):
    ruta = f"/api/actividades/{limpieza_de_hoy['id_actividad']}"
    exigir(api_voluntario.post(f"{ruta}/completar", json={}))

    assert api_voluntario.post(f"{ruta}/reabrir").status_code == 403
    assert exigir(api_manejo.post(f"{ruta}/reabrir"))["completada"] is False


def test_quien_programo_queda_registrado(usuarios, limpieza_de_hoy):
    assert limpieza_de_hoy["id_usuario_programo"] == usuarios["manejo"].id_usuario


# ---------- Fichas: diagnósticos y tratamientos son de Veterinaria ----------

def test_manejo_de_animales_no_registra_diagnosticos_403(api_manejo, animal):
    respuesta = api_manejo.post(f"/api/animales/{animal['id_animal']}/diagnosticos", json={"diagnostico": "Fiebre"})

    assert respuesta.status_code == 403


def test_manejo_de_animales_no_crea_tratamientos_403(api_manejo, diagnostico):
    respuesta = api_manejo.post(
        f"/api/animales/diagnosticos/{diagnostico['id_diagnostico']}/tratamientos",
        json={"descripcion": "x", "frecuencia_valor": 1, "frecuencia_unidad": "dias", "hora_inicio": "09:00:00"},
    )

    assert respuesta.status_code == 403


def test_veterinaria_si_registra_fichas(api_veterinaria, taxonomia, recinto):
    animal = exigir(
        api_veterinaria.post(
            "/api/animales",
            json={
                "id_taxonomia": taxonomia["id_taxonomia"],
                "id_recinto": recinto["id_recinto"],
                "edad_anios": 1,
                "edad_meses": 0,
            },
        ),
        201,
    )

    assert animal["codigo_animal"].startswith("YC-")


def test_voluntario_no_registra_animales_403(api_voluntario, taxonomia, recinto):
    respuesta = api_voluntario.post(
        "/api/animales",
        json={"id_taxonomia": taxonomia["id_taxonomia"], "id_recinto": recinto["id_recinto"], "edad_anios": 1, "edad_meses": 0},
    )

    assert respuesta.status_code == 403
