import importlib

import dotenv
import pytest

import src.config


@pytest.fixture
def recargar_config(monkeypatch):
    """Recarga src.config con las variables de entorno del test, ignorando el .env local."""
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)

    def _recargar():
        return importlib.reload(src.config)

    yield _recargar

    # Restauramos la configuración original para no afectar a otros tests
    monkeypatch.undo()
    importlib.reload(src.config)


def test_valores_por_defecto(recargar_config, monkeypatch):
    for variable in ("ACCESSOS_SERVICE_URL", "CORS_ORIGINS", "PROXY_TIMEOUT_SECONDS"):
        monkeypatch.delenv(variable, raising=False)

    config = recargar_config()

    assert config.ACCESSOS_SERVICE_URL == "http://localhost:8001"
    assert config.CORS_ORIGINS == ["http://localhost:5173"]
    assert config.PROXY_TIMEOUT_SECONDS == 10.0


def test_lee_url_del_servicio_desde_el_entorno(recargar_config, monkeypatch):
    monkeypatch.setenv("ACCESSOS_SERVICE_URL", "http://accesos:9000")

    assert recargar_config().ACCESSOS_SERVICE_URL == "http://accesos:9000"


def test_cors_origins_separa_por_coma_y_limpia_espacios(recargar_config, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", " http://a.com , http://b.com,, ")

    assert recargar_config().CORS_ORIGINS == ["http://a.com", "http://b.com"]


def test_timeout_se_convierte_a_float(recargar_config, monkeypatch):
    monkeypatch.setenv("PROXY_TIMEOUT_SECONDS", "2.5")

    assert recargar_config().PROXY_TIMEOUT_SECONDS == 2.5


def test_timeout_invalido_falla_al_iniciar(recargar_config, monkeypatch):
    monkeypatch.setenv("PROXY_TIMEOUT_SECONDS", "no-es-numero")

    with pytest.raises(ValueError):
        recargar_config()


def test_lee_secret_key_y_algoritmo_desde_el_entorno(recargar_config, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "otra-clave")
    monkeypatch.setenv("ALGORITHM", "HS512")

    config = recargar_config()

    assert (config.SECRET_KEY, config.ALGORITHM) == ("otra-clave", "HS512")


def test_algoritmo_por_defecto_es_hs256(recargar_config, monkeypatch):
    monkeypatch.delenv("ALGORITHM", raising=False)

    assert recargar_config().ALGORITHM == "HS256"


@pytest.mark.parametrize("valor", [None, ""])
def test_sin_secret_key_falla_al_iniciar(recargar_config, monkeypatch, valor):
    # No hay valor por defecto: evita firmar o validar tokens con un secreto conocido
    if valor is None:
        monkeypatch.delenv("SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("SECRET_KEY", valor)

    with pytest.raises(RuntimeError):
        recargar_config()
