import pytest

from src.logica_negocio.codigo_animal import iniciales, siguiente_codigo


@pytest.mark.parametrize("nombre,esperado", [
    ("Canis lupus familiaris", "CLF"),
    ("Tremarctos ornatus", "TO"),
    ("  vultur   gryphus ", "VG"),
    ("Ateles fusciceps-robustus", "AFR"),  # el guion separa palabras
    ("Pudú mephistophiles", "PM"),  # sin tildes
    ("123", ""),
])
def test_iniciales_del_nombre_cientifico(nombre, esperado):
    assert iniciales(nombre) == esperado


def test_primer_codigo_de_un_prefijo():
    assert siguiente_codigo("CLF", []) == "CLF-001"


def test_sigue_desde_el_numero_mas_alto():
    # Aunque falte el 002, nunca se reutiliza un número
    assert siguiente_codigo("CLF", ["CLF-001", "CLF-003"]) == "CLF-004"


def test_ignora_otros_prefijos_y_codigos_mal_formados():
    assert siguiente_codigo("CL", ["CLF-009", "CL-002", "CL-abc"]) == "CL-003"


def test_mas_de_999_sigue_creciendo():
    assert siguiente_codigo("TO", ["TO-999"]) == "TO-1000"
