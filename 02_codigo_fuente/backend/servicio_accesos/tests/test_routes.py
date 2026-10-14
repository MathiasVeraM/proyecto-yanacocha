import pytest

from tests.conftest import PASSWORD

NUEVO = {"nombre": "Luis", "apellido": "Gómez", "correo": "luis@test.com", "password": PASSWORD, "id_rol": 2}

ENDPOINTS_ADMIN = [
    ("GET", "/api/auth/usuarios", None),
    ("POST", "/api/auth/usuarios", NUEVO),
    ("PUT", "/api/auth/usuarios/1", {"nombre": "X"}),
    ("PATCH", "/api/auth/usuarios/1/desactivar", None),
    ("POST", "/api/auth/roles", {"nombre_rol": "Vet"}),
    ("POST", "/api/auth/modulos", {"nombre_modulo": "M", "codigo_servicio": "m"}),
]


@pytest.mark.parametrize("metodo,url,cuerpo", ENDPOINTS_ADMIN)
def test_admin_sin_token_401(client, metodo, url, cuerpo):
    assert client.request(metodo, url, json=cuerpo).status_code == 401


@pytest.mark.parametrize("metodo,url,cuerpo", ENDPOINTS_ADMIN)
def test_admin_con_rol_no_admin_403(client, headers_no_admin, metodo, url, cuerpo):
    assert client.request(metodo, url, json=cuerpo, headers=headers_no_admin).status_code == 403


@pytest.mark.parametrize("url", ["/api/auth/roles", "/api/auth/modulos"])
def test_listados_publicos(client, url):
    assert client.get(url).status_code == 200


def test_login_ok(client, crear_usuario_db):
    crear_usuario_db()
    resp = client.post("/api/auth/login", json={"correo": "user@test.com", "password": PASSWORD})
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer" and resp.json()["access_token"]


def test_login_desactivado_403(client, crear_usuario_db):
    crear_usuario_db(activo=False)
    resp = client.post("/api/auth/login", json={"correo": "user@test.com", "password": PASSWORD})
    assert resp.status_code == 403


def test_login_credenciales_incorrectas_401(client):
    resp = client.post("/api/auth/login", json={"correo": "no@test.com", "password": PASSWORD})
    assert resp.status_code == 401


def test_login_correo_invalido_422(client):
    assert client.post("/api/auth/login", json={"correo": "x", "password": "y"}).status_code == 422


def test_crear_usuario_201_sin_password_hash(client, headers_admin):
    resp = client.post("/api/auth/usuarios", json=NUEVO, headers=headers_admin)
    assert resp.status_code == 201
    assert "password_hash" not in resp.json() and "password" not in resp.json()


def test_crear_usuario_password_corta_422(client, headers_admin):
    resp = client.post("/api/auth/usuarios", json={**NUEVO, "password": "corta"}, headers=headers_admin)
    assert resp.status_code == 422


def test_crear_usuario_duplicado_400(client, headers_admin):
    client.post("/api/auth/usuarios", json=NUEVO, headers=headers_admin)
    assert client.post("/api/auth/usuarios", json=NUEVO, headers=headers_admin).status_code == 400


def test_listar_usuarios(client, headers_admin, crear_usuario_db):
    crear_usuario_db()
    resp = client.get("/api/auth/usuarios", headers=headers_admin)
    assert resp.status_code == 200 and len(resp.json()) == 1
    assert "password_hash" not in resp.json()[0]


def test_actualizar_usuario(client, headers_admin, crear_usuario_db):
    u = crear_usuario_db()
    resp = client.put(f"/api/auth/usuarios/{u.id_usuario}", json={"nombre": "Nuevo"}, headers=headers_admin)
    assert resp.status_code == 200 and resp.json()["nombre"] == "Nuevo"


def test_actualizar_inexistente_404(client, headers_admin):
    assert client.put("/api/auth/usuarios/999", json={"nombre": "X"}, headers=headers_admin).status_code == 404


def test_desactivar_usuario(client, headers_admin, crear_usuario_db):
    u = crear_usuario_db()
    resp = client.patch(f"/api/auth/usuarios/{u.id_usuario}/desactivar", headers=headers_admin)
    assert resp.status_code == 200 and resp.json()["activo"] is False


def test_desactivar_inexistente_404(client, headers_admin):
    assert client.patch("/api/auth/usuarios/999/desactivar", headers=headers_admin).status_code == 404


def test_crear_rol_201_y_duplicado_400(client, headers_admin):
    cuerpo = {"nombre_rol": "Veterinario"}
    assert client.post("/api/auth/roles", json=cuerpo, headers=headers_admin).status_code == 201
    assert client.post("/api/auth/roles", json=cuerpo, headers=headers_admin).status_code == 400
    assert len(client.get("/api/auth/roles").json()) == 3


def test_crear_modulo_201_y_duplicado_400(client, headers_admin):
    cuerpo = {"nombre_modulo": "Animales", "codigo_servicio": "animales"}
    assert client.post("/api/auth/modulos", json=cuerpo, headers=headers_admin).status_code == 201
    assert client.post("/api/auth/modulos", json=cuerpo, headers=headers_admin).status_code == 400
    assert len(client.get("/api/auth/modulos").json()) == 1
