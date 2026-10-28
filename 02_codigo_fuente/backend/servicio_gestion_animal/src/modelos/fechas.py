from datetime import date, datetime

from src.config import ZONA_HORARIA


def hoy_local() -> date:
    return datetime.now(ZONA_HORARIA).date()


def ahora_local() -> datetime:
    return datetime.now(ZONA_HORARIA).replace(tzinfo=None)
