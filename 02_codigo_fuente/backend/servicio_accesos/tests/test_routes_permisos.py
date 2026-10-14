import pytest

ENDPOINTS_ADMIN = [
    ("PUT", "/api/auth/roles/2", {"descripcion": "x"}),
    ("DELETE", "/api/auth/roles/2", None),
    ("PUT", "/api/auth/modulos/1", {"nombre_modulo": "X"}),
    ("DELETE", "/api/auth/modulos/1", None),
    ("GET", "/api/auth/permisos/matriz", None),
    ("PUT", "/api/auth/permisos/2/1", None),
    ("DELETE", "/api/auth/permisos/2/1", None),
]


@pytest.mark.parametrize("metodo,url,cuerpo", ENDPOINTS_ADMIN)
def test_sin_token_401(client, metodo, url, cuerpo):
    assert client.request(metodo, url, json=cuerpo).status_code == 401


@pytest.mark.parametrize("metodo,url,cuerpo", ENDPOINTS_ADMIN)
def test_rol_no_admin_403(client, headers_no_admin, metodo, url, cuerpo):
    assert client.request(metodo, url, json=cuerpo, headers=headers_no_admin).status_code == 403


# --- Roles ---

def test_editar_rol(client, headers_admin):
    resp = client.put("/api/auth/roles/2", json={"nombre_rol": "Veterinaria", "descripcion": "Vet"}, headers=headers_admin)
    assert resp.status_code == 200
    assert resp.json()["nombre_rol"] == "Veterinaria" and resp.json()["descripcion"] == "Vet"


def test_editar_rol_inexistente_404(client, headers_admin):
    assert client.put("/api/auth/roles/999", json={"descripcion": "x"}, headers=headers_admin).status_code == 404


def test_editar_rol_nombre_duplicado_400(client, headers_admin):
    resp = client.put("/api/auth/roles/2", json={"nombre_rol": "Administrador"}, headers=headers_admin)
    assert resp.status_code == 400


def test_editar_rol_nombre_vacio_422(client, headers_admin):
    assert client.put("/api/auth/roles/2", json={"nombre_rol": ""}, headers=headers_admin).status_code == 422


def test_eliminar_rol(client, headers_admin):
    assert client.delete("/api/auth/roles/2", headers=headers_admin).status_code == 204
    ids = [r["id_rol"] for r in client.get("/api/auth/roles").json()]
    assert 2 not in ids


def test_eliminar_rol_inexistente_404(client, headers_admin):
    assert client.delete("/api/auth/roles/999", headers=headers_admin).status_code == 404


def test_eliminar_rol_administrador_409(client, headers_admin):
    assert client.delete("/api/auth/roles/1", headers=headers_admin).status_code == 409


def test_eliminar_rol_con_usuarios_409(client, headers_admin, crear_usuario_db):
    crear_usuario_db(id_rol=2)
    assert client.delete("/api/auth/roles/2", headers=headers_admin).status_code == 409


# --- Módulos ---

def test_editar_modulo(client, headers_admin, crear_modulo_db):
    modulo = crear_modulo_db()
    resp = client.put(
        f"/api/auth/modulos/{modulo.id_modulo}",
        json={"nombre_modulo": "Planificación", "codigo_servicio": "servicio-actividades"},
        headers=headers_admin,
    )
    assert resp.status_code == 200
    assert resp.json()["nombre_modulo"] == "Planificación"
    assert resp.json()["codigo_servicio"] == "servicio-actividades"


def test_editar_modulo_inexistente_404(client, headers_admin):
    assert client.put("/api/auth/modulos/999", json={"nombre_modulo": "X"}, headers=headers_admin).status_code == 404


def test_editar_modulo_nombre_duplicado_400(client, headers_admin, crear_modulo_db):
    crear_modulo_db("M1", "m1")
    m2 = crear_modulo_db("M2", "m2")
    resp = client.put(f"/api/auth/modulos/{m2.id_modulo}", json={"nombre_modulo": "M1"}, headers=headers_admin)
    assert resp.status_code == 400


def test_eliminar_modulo(client, headers_admin, crear_modulo_db):
    modulo = crear_modulo_db()
    assert client.delete(f"/api/auth/modulos/{modulo.id_modulo}", headers=headers_admin).status_code == 204
    assert client.get("/api/auth/modulos").json() == []


def test_eliminar_modulo_inexistente_404(client, headers_admin):
    assert client.delete("/api/auth/modulos/999", headers=headers_admin).status_code == 404


def test_eliminar_modulo_quita_sus_permisos_de_la_matriz(client, headers_admin, crear_modulo_db):
    modulo = crear_modulo_db()
    client.put(f"/api/auth/permisos/2/{modulo.id_modulo}", headers=headers_admin)
    client.delete(f"/api/auth/modulos/{modulo.id_modulo}", headers=headers_admin)
    assert client.get("/api/auth/permisos/matriz", headers=headers_admin).json()["permisos"] == []


# --- Permisos ---

def test_asignar_permiso(client, headers_admin, crear_modulo_db):
    modulo = crear_modulo_db()
    resp = client.put(f"/api/auth/permisos/2/{modulo.id_modulo}", headers=headers_admin)
    assert resp.status_code == 200
    assert resp.json() == {"id_rol": 2, "id_modulo": modulo.id_modulo}


def test_asignar_permiso_es_idempotente(client, headers_admin, crear_modulo_db):
    modulo = crear_modulo_db()
    url = f"/api/auth/permisos/2/{modulo.id_modulo}"
    assert client.put(url, headers=headers_admin).status_code == 200
    assert client.put(url, headers=headers_admin).status_code == 200
    permisos = client.get("/api/auth/permisos/matriz", headers=headers_admin).json()["permisos"]
    assert permisos == [{"id_rol": 2, "id_modulo": modulo.id_modulo}]


def test_asignar_permiso_rol_inexistente_404(client, headers_admin, crear_modulo_db):
    modulo = crear_modulo_db()
    assert client.put(f"/api/auth/permisos/999/{modulo.id_modulo}", headers=headers_admin).status_code == 404


def test_asignar_permiso_modulo_inexistente_404(client, headers_admin):
    assert client.put("/api/auth/permisos/2/999", headers=headers_admin).status_code == 404


def test_quitar_permiso(client, headers_admin, crear_modulo_db):
    modulo = crear_modulo_db()
    url = f"/api/auth/permisos/2/{modulo.id_modulo}"
    client.put(url, headers=headers_admin)
    assert client.delete(url, headers=headers_admin).status_code == 204
    assert client.get("/api/auth/permisos/matriz", headers=headers_admin).json()["permisos"] == []


def test_quitar_permiso_inexistente_es_idempotente(client, headers_admin, crear_modulo_db):
    modulo = crear_modulo_db()
    assert client.delete(f"/api/auth/permisos/2/{modulo.id_modulo}", headers=headers_admin).status_code == 204


def test_quitar_permiso_rol_o_modulo_inexistente_404(client, headers_admin, crear_modulo_db):
    modulo = crear_modulo_db()
    assert client.delete(f"/api/auth/permisos/999/{modulo.id_modulo}", headers=headers_admin).status_code == 404
    assert client.delete("/api/auth/permisos/2/999", headers=headers_admin).status_code == 404


def test_quitar_permiso_al_administrador_409(client, headers_admin, crear_modulo_db):
    modulo = crear_modulo_db()
    url = f"/api/auth/permisos/1/{modulo.id_modulo}"
    client.put(url, headers=headers_admin)
    assert client.delete(url, headers=headers_admin).status_code == 409


# --- Matriz ---

def test_matriz(client, headers_admin, crear_modulo_db, crear_usuario_db):
    modulo = crear_modulo_db()
    crear_usuario_db(id_rol=2)
    client.put(f"/api/auth/permisos/1/{modulo.id_modulo}", headers=headers_admin)

    resp = client.get("/api/auth/permisos/matriz", headers=headers_admin)

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert set(cuerpo) == {"roles", "modulos", "permisos"}
    assert {r["id_rol"]: r["total_usuarios"] for r in cuerpo["roles"]} == {1: 0, 2: 1}
    assert [m["id_modulo"] for m in cuerpo["modulos"]] == [modulo.id_modulo]
    assert cuerpo["permisos"] == [{"id_rol": 1, "id_modulo": modulo.id_modulo}]
