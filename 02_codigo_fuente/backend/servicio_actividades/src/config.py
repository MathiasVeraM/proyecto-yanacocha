import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta la variable de entorno DATABASE_URL")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Falta la variable de entorno SECRET_KEY")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
DB_SCHEMA = "actividades"
ZONA_HORARIA = ZoneInfo("America/Guayaquil")
HORIZONTE_TOMAS_DIAS = int(os.getenv("HORIZONTE_TOMAS_DIAS", "30"))
if HORIZONTE_TOMAS_DIAS < 1:
    raise RuntimeError("HORIZONTE_TOMAS_DIAS debe ser mayor que cero")
