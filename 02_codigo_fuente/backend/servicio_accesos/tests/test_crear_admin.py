import pytest

import crear_admin as modulo
from src.logica_negocio.auth import verify_password
from src.repositorios.usuario_repo import UsuarioRepository


def test_crea_admin(db):
    assert modulo.crear_admin(db, "admin@test.com", "password123") is True
    admin = UsuarioRepository.obtener_por_correo(db, "admin@test.com")
    assert admin.id_rol == modulo.ID_ROL_ADMIN and admin.activo is True
    assert verify_password("password123", admin.password_hash)


def test_admin_repetido_devuelve_false(db):
    modulo.crear_admin(db, "admin@test.com", "password123")
    assert modulo.crear_admin(db, "admin@test.com", "password123") is False
    assert len(UsuarioRepository.obtener_todos(db)) == 1


def test_password_corta_lanza_value_error(db):
    with pytest.raises(ValueError):
        modulo.crear_admin(db, "admin@test.com", "corta")


def test_main_sin_variables_devuelve_1(monkeypatch):
    monkeypatch.delenv("ADMIN_CORREO", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    assert modulo.main() == 1


def test_main_password_corta_devuelve_1(monkeypatch, session_factory):
    monkeypatch.setenv("ADMIN_CORREO", "admin@test.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "corta")
    monkeypatch.setattr(modulo, "SessionLocal", session_factory)
    assert modulo.main() == 1


def test_main_crea_y_luego_informa_existente(monkeypatch, session_factory, db, capsys):
    monkeypatch.setenv("ADMIN_CORREO", "admin@test.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "password123")
    monkeypatch.setattr(modulo, "SessionLocal", session_factory)
    assert modulo.main() == 0
    assert "creado con éxito" in capsys.readouterr().out
    assert modulo.main() == 0
    assert "ya existe" in capsys.readouterr().out
