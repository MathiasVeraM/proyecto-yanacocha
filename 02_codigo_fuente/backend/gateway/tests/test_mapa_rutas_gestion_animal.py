"""Pruebas del mapa de rutas para el servicio de gestión animal."""
import importlib

import dotenv
import pytest

import src.config
from src.mapa_rutas import NIVEL_MODULO, resolver_regla
from src.modulos import MODULO_FICHAS_EJEMPLARES


@pytest.mark.parametrize(
    "metodo,ruta",
    [
        ("GET", "/api/animales"),
        ("GET", "/api/animales/"),
        ("POST", "/api/animales"),
        ("GET", "/api/animales/3"),
        ("PUT", "/api/animales/3"),
        ("DELETE", "/api/animales/3"),
        ("GET", "/api/animales/3/diagnosticos"),
        ("POST", "/api/animales/3/diagnosticos"),
        ("PUT", "/api/animales/diagnosticos/4"),
        ("GET", "/api/animales/diagnosticos/4/tratamientos"),
        ("PUT", "/api/animales/tratamientos/5"),
    ],
)
def test_rutas_de_animales_exigen_el_modulo_de_fichas(metodo, ruta):
    regla = resolver_regla(metodo, ruta)

    assert regla.nivel == NIVEL_MODULO
    assert regla.codigo_servicio == MODULO_FICHAS_EJEMPLARES


@pytest.mark.parametrize("ruta", ["/api/animalesx", "/api/animal", "/api/animales-otro/1"])
def test_prefijos_parecidos_no_pertenecen_a_gestion_animal(ruta):
    assert resolver_regla("GET", ruta) is None


def test_url_de_gestion_animal_por_defecto_y_desde_el_entorno(monkeypatch):
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
    try:
        monkeypatch.delenv("GESTION_ANIMAL_SERVICE_URL", raising=False)
        assert importlib.reload(src.config).GESTION_ANIMAL_SERVICE_URL == "http://localhost:8002"

        monkeypatch.setenv("GESTION_ANIMAL_SERVICE_URL", "http://gestion-animal:9000")
        assert importlib.reload(src.config).GESTION_ANIMAL_SERVICE_URL == "http://gestion-animal:9000"
    finally:
        # Restauramos la configuración original para no afectar a otros tests
        monkeypatch.undo()
        importlib.reload(src.config)
