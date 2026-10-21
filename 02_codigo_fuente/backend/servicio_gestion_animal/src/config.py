import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta la variable de entorno DATABASE_URL")

# Clave con la que accesos firma los tokens.
# Sin valor por defecto: si falta, el servicio no arranca.
# Debe ser igual a la del servicio de accesos y la del gateway.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Falta la variable de entorno SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Esquema de la base de datos donde viven las tablas de este servicio
DB_SCHEMA = "gestion_animal"

# Debe coincidir con la columna codigo_servicio de la tabla modulo
CODIGO_MODULO = "servicio-gestion-animal"
ID_ROL_ADMIN = 1

# El servidor de la base de datos está en UTC; las fechas se calculan en hora del centro
ZONA_HORARIA = ZoneInfo("America/Guayaquil")

# API pública y gratuita de iNaturalist para sugerir especies por nombre común en español
INATURALIST_URL = os.getenv("INATURALIST_URL", "https://api.inaturalist.org/v1")
# Si iNaturalist tarda más, se responde solo con el catálogo propio
INATURALIST_TIMEOUT_SECONDS = float(os.getenv("INATURALIST_TIMEOUT_SECONDS", "3"))
