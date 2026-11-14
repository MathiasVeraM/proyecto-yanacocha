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

# Deben coincidir con los id_rol de la tabla rol del servicio de accesos
ID_ROL_VETERINARIA = 2
ID_ROL_MANEJO_ANIMAL = 3
ID_ROL_VOLUNTARIO = 4
ZONA_HORARIA = ZoneInfo("America/Guayaquil")
HORIZONTE_TOMAS_DIAS = int(os.getenv("HORIZONTE_TOMAS_DIAS", "30"))
if HORIZONTE_TOMAS_DIAS < 1:
    raise RuntimeError("HORIZONTE_TOMAS_DIAS debe ser mayor que cero")

# ---- Límites de las actividades y dietas (los decide el centro) ----
# Se definen solo aquí; el frontend los consulta en GET /api/actividades/limites
def _entero_positivo(nombre: str, predeterminado: int) -> int:
    valor = int(os.getenv(nombre, str(predeterminado)))
    if valor < 1:
        raise RuntimeError(f"{nombre} debe ser mayor que cero")
    return valor


# Hasta cuántos días hacia el futuro se puede programar una actividad (1 año)
ACTIVIDAD_DIAS_FUTURO_MAX = _entero_positivo("ACTIVIDAD_DIAS_FUTURO_MAX", 365)
# Duración máxima de cualquier actividad, en minutos (4 horas)
DURACION_MAX_MINUTOS = _entero_positivo("DURACION_MAX_MINUTOS", 240)
# Duración que toma un enriquecimiento si no se indica (para poder revisar cruces)
DURACION_ENRIQUECIMIENTO_MINUTOS = _entero_positivo("DURACION_ENRIQUECIMIENTO_MINUTOS", 30)
# Duración que se asume al revisar cruces cuando la actividad no tiene duración (ej. una toma)
DURACION_MINIMA_CRUCE_MINUTOS = _entero_positivo("DURACION_MINIMA_CRUCE_MINUTOS", 15)
# Máximo de meses que puede abarcar una actividad repetida
REPETICION_MESES_MAX = _entero_positivo("REPETICION_MESES_MAX", 3)
# Hasta cuántos días hacia el futuro puede empezar una dieta nueva
DIETA_INICIO_DIAS_FUTURO_MAX = _entero_positivo("DIETA_INICIO_DIAS_FUTURO_MAX", 30)
