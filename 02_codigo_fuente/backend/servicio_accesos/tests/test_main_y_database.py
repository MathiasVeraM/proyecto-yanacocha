from unittest.mock import MagicMock

import pytest

from src import database


def test_raiz_responde(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Servicio de Accesos operativo"}


def test_get_db_entrega_y_cierra_la_sesion(monkeypatch):
    sesion = MagicMock()
    monkeypatch.setattr(database, "SessionLocal", lambda: sesion)
    gen = database.get_db()
    assert next(gen) is sesion
    gen.close()
    sesion.close.assert_called_once()


def test_get_db_cierra_la_sesion_ante_excepcion(monkeypatch):
    sesion = MagicMock()
    monkeypatch.setattr(database, "SessionLocal", lambda: sesion)
    gen = database.get_db()
    next(gen)
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("fallo"))
    sesion.close.assert_called_once()
