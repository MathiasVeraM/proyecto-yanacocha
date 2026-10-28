import pytest

from src.logica_negocio.codigo_animal import iniciales, siguiente_codigo


@pytest.mark.parametrize("nombre,esperado", [
    ("Canis lupus familiaris", "CLF"),
    ("Tremarctos ornatus", "TO"),
    ("  vultur   gryphus ", "VG"),
    ("Ateles fusciceps-robustus", "AFR"),
    ("Pudú mephistophiles", "PM"),
    ("123", ""),
])
def test_iniciales_del_nombre_cientifico(nombre, esperado):
    assert iniciales(nombre) == esperado


def test_primer_codigo_del_anio():
    assert siguiente_codigo("YC-2026", []) == "YC-2026-0001"


def test_sigue_desde_el_numero_mas_alto_del_anio():
    # Aunque falte un número, nunca se reutiliza un código
    assert siguiente_codigo("YC-2026", ["YC-2026-0001", "YC-2026-0003"]) == "YC-2026-0004"


def test_ignora_otros_anios_y_codigos_mal_formados():
    assert siguiente_codigo("YC-2026", ["YC-2025-0099", "YC-2026-0002", "YC-2026-abc"]) == "YC-2026-0003"


def test_mas_de_9999_sigue_creciendo():
    assert siguiente_codigo("YC-2026", ["YC-2026-9999"]) == "YC-2026-10000"
