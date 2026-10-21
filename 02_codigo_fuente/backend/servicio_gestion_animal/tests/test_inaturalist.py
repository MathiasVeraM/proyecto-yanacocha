# Se importa antes de que el fixture autouse lo reemplace, para revisar el cliente real sin usar la red
from src.logica_negocio.inaturalist import crear_cliente as crear_cliente_real
from src.config import INATURALIST_TIMEOUT_SECONDS


def test_cliente_real_apunta_a_inaturalist_con_timeout_corto():
    with crear_cliente_real() as cliente:
        assert str(cliente.base_url).rstrip("/") == "https://api.inaturalist.org/v1"
        assert cliente.timeout.read == INATURALIST_TIMEOUT_SECONDS == 3
        # iNaturalist pide identificar a la aplicación que consulta su API
        assert cliente.headers["User-Agent"] == "Yanacocha-GestionAnimal/1.0"
