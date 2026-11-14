"""Reglas de las actividades que programa una persona (no las tomas ni dosis que genera el sistema).

- No se programa en el pasado: desde este momento hasta ACTIVIDAD_DIAS_FUTURO_MAX días.
- Duración máxima DURACION_MAX_MINUTOS; el enriquecimiento sin duración toma una por defecto.
- Duplicado exacto (mismo tipo, animal o recinto, día y hora; en alimentación, misma dieta): 409.
- Cruce de horario con otra actividad del mismo animal o recinto: 409 con la lista de cruces,
  salvo que la persona confirme ("crear igual").
- Repetición: todos los días o ciertos días, hasta una fecha o durante N meses.
"""
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.config import (
    ACTIVIDAD_DIAS_FUTURO_MAX,
    DIETA_INICIO_DIAS_FUTURO_MAX,
    DURACION_ENRIQUECIMIENTO_MINUTOS,
    DURACION_MAX_MINUTOS,
    DURACION_MINIMA_CRUCE_MINUTOS,
    REPETICION_MESES_MAX,
)
from src.modelos.actividad_model import ActividadModel
from src.modelos.fechas import ahora_local

CODIGO_CRUCE = "cruce_horario"


def ahora() -> datetime:
    # Punto único para "ahora" en estas reglas (las pruebas lo fijan en una fecha conocida)
    return ahora_local()


def limites() -> dict:
    """Los límites vigentes, para que el frontend los use como min y max de los campos."""
    momento = ahora()
    hoy = momento.date()
    return {
        "hoy": hoy,
        "hora_actual": momento.time().replace(second=0, microsecond=0),
        "fecha_min": hoy,
        "fecha_max": hoy + timedelta(days=ACTIVIDAD_DIAS_FUTURO_MAX),
        "duracion_max_minutos": DURACION_MAX_MINUTOS,
        "duracion_enriquecimiento_minutos": DURACION_ENRIQUECIMIENTO_MINUTOS,
        "repeticion_meses_max": REPETICION_MESES_MAX,
        "dieta_inicio_fecha_max": hoy + timedelta(days=DIETA_INICIO_DIAS_FUTURO_MAX),
    }


def _error(codigo: int, detalle) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalle)


# ---- Fecha y duración ----

def validar_fecha(fecha: date, hora: time | None) -> None:
    momento = ahora()
    hoy = momento.date()
    actual = momento.time().replace(second=0, microsecond=0)
    if fecha < hoy or (fecha == hoy and hora is not None and hora < actual):
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "No se pueden programar actividades en el pasado",
        )
    if fecha > hoy + timedelta(days=ACTIVIDAD_DIAS_FUTURO_MAX):
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Solo se pueden programar actividades hasta {ACTIVIDAD_DIAS_FUTURO_MAX} días hacia adelante",
        )


def validar_duracion(tipo: str, datos: dict) -> None:
    """Revisa el máximo y completa la duración por defecto del enriquecimiento (modifica datos)."""
    total = datos.get("duracion_horas", 0) * 60 + datos.get("duracion_minutos", 0)
    if tipo == "enriquecimiento" and total == 0:
        total = DURACION_ENRIQUECIMIENTO_MINUTOS
        datos["duracion_horas"], datos["duracion_minutos"] = divmod(total, 60)
    if total > DURACION_MAX_MINUTOS:
        horas, minutos = divmod(DURACION_MAX_MINUTOS, 60)
        texto = f"{horas} horas" + (f" y {minutos} minutos" if minutos else "")
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"La duración máxima de una actividad es de {texto}",
        )


# ---- Duplicados y cruces ----
# Se trabaja con las actividades del mismo ejemplar o recinto traídas en UNA consulta
# (relacionadas) y se compara en memoria: con la base remota, una consulta por fecha de una
# repetición larga superaría el tiempo de espera del gateway.

def actividades_relacionadas(db: Session, datos: dict, desde: date, hasta: date) -> list:
    """Actividades del mismo ejemplar o del mismo recinto entre dos fechas."""
    filtros = []
    if datos.get("id_animal") is not None:
        filtros.append(ActividadModel.id_animal == datos["id_animal"])
    if datos.get("id_recinto") is not None:
        filtros.append(ActividadModel.id_recinto == datos["id_recinto"])
    if not filtros:
        return []
    return (
        db.query(ActividadModel)
        .filter(
            ActividadModel.fecha_programada >= desde,
            ActividadModel.fecha_programada <= hasta,
            or_(*filtros),
        )
        .all()
    )


def es_duplicado(otra, tipo: str, datos: dict) -> bool:
    if (
        otra.tipo_actividad != tipo
        or otra.fecha_programada != datos["fecha_programada"]
        or otra.hora_programada != datos.get("hora_programada")
    ):
        return False
    if tipo == "alimentacion":
        # Una alimentación manual no puede repetir una toma de la misma dieta en el mismo día y hora
        return otra.alimentacion is not None and otra.alimentacion.id_dieta == datos["id_dieta"]
    if tipo == "limpieza":
        return otra.id_recinto == datos["id_recinto"]
    return otra.id_animal == datos["id_animal"]


def mensaje_duplicado(tipo: str) -> str:
    if tipo == "alimentacion":
        return "Ya existe una toma de esa dieta en el mismo día y hora"
    return "Ya existe una actividad igual (mismo tipo, ejemplar o recinto, día y hora)"


def verificar_duplicado(
    db: Session,
    tipo: str,
    datos: dict,
    excluir_id: int | None = None,
    relacionadas: list | None = None,
) -> None:
    if relacionadas is None:
        relacionadas = actividades_relacionadas(db, datos, datos["fecha_programada"], datos["fecha_programada"])
    if any(o.id_actividad != excluir_id and es_duplicado(o, tipo, datos) for o in relacionadas):
        raise _error(status.HTTP_409_CONFLICT, mensaje_duplicado(tipo))


def _minutos(actividad_o_datos) -> int:
    if isinstance(actividad_o_datos, dict):
        total = actividad_o_datos.get("duracion_horas", 0) * 60 + actividad_o_datos.get("duracion_minutos", 0)
    else:
        total = actividad_o_datos.duracion_horas * 60 + actividad_o_datos.duracion_minutos
    return max(total, DURACION_MINIMA_CRUCE_MINUTOS)


def se_cruza(otra, datos: dict) -> bool:
    hora = datos.get("hora_programada")
    if hora is None or otra.hora_programada is None or otra.fecha_programada != datos["fecha_programada"]:
        return False
    if not (
        (datos.get("id_animal") is not None and otra.id_animal == datos["id_animal"])
        or (datos.get("id_recinto") is not None and otra.id_recinto == datos["id_recinto"])
    ):
        return False
    inicio = datetime.combine(datos["fecha_programada"], hora)
    fin = inicio + timedelta(minutes=_minutos(datos))
    otra_inicio = datetime.combine(otra.fecha_programada, otra.hora_programada)
    otra_fin = otra_inicio + timedelta(minutes=_minutos(otra))
    return otra_inicio < fin and inicio < otra_fin


def buscar_cruces(
    db: Session,
    datos: dict,
    excluir_id: int | None = None,
    relacionadas: list | None = None,
) -> list:
    """Actividades del mismo ejemplar (o del mismo recinto, en limpieza) que se cruzan en horario."""
    if datos.get("hora_programada") is None:
        return []
    if relacionadas is None:
        relacionadas = actividades_relacionadas(db, datos, datos["fecha_programada"], datos["fecha_programada"])
    return [o for o in relacionadas if o.id_actividad != excluir_id and se_cruza(o, datos)]


def error_cruce(cruces: list) -> HTTPException:
    """409 que el frontend reconoce para preguntar "¿crear igual?"."""
    return _error(
        status.HTTP_409_CONFLICT,
        {
            "codigo": CODIGO_CRUCE,
            "mensaje": "La actividad se cruza en horario con otras del mismo ejemplar o recinto",
            "cruces": [
                {
                    "id_actividad": a.id_actividad,
                    "tipo_actividad": a.tipo_actividad,
                    "fecha_programada": a.fecha_programada.isoformat(),
                    "hora_programada": a.hora_programada.strftime("%H:%M") if a.hora_programada else None,
                    "duracion_minutos": a.duracion_horas * 60 + a.duracion_minutos,
                }
                for a in cruces
            ],
        },
    )


# ---- Repetición ----

def _sumar_meses(fecha: date, meses: int) -> date:
    mes = fecha.month - 1 + meses
    anio = fecha.year + mes // 12
    mes = mes % 12 + 1
    # Si el día no existe en ese mes (ej. 31 de abril), se usa el último día del mes
    dia = fecha.day
    while True:
        try:
            return date(anio, mes, dia)
        except ValueError:
            dia -= 1


def fechas_de_repeticion(
    inicio: date,
    dias_semana: list[int] | None,
    fecha_fin: date | None,
    meses: int | None,
) -> list[date]:
    """Fechas de una actividad repetida. dias_semana: 0 = lunes … 6 = domingo; None = todos los días."""
    if (fecha_fin is None) == (meses is None):
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Indica hasta qué fecha se repite o durante cuántos meses",
        )
    limite = _sumar_meses(inicio, REPETICION_MESES_MAX)
    if meses is not None:
        if meses < 1 or meses > REPETICION_MESES_MAX:
            raise _error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"La repetición puede durar de 1 a {REPETICION_MESES_MAX} meses",
            )
        fecha_fin = _sumar_meses(inicio, meses) - timedelta(days=1)
    if fecha_fin < inicio:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "La fecha de fin de la repetición no puede ser anterior al primer día",
        )
    if fecha_fin > limite:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"La repetición puede durar como máximo {REPETICION_MESES_MAX} meses",
        )
    dias = set(dias_semana) if dias_semana else None
    if dias is not None and not dias <= set(range(7)):
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Días de la semana no válidos")
    fechas = []
    actual = inicio
    while actual <= fecha_fin:
        if dias is None or actual.weekday() in dias:
            fechas.append(actual)
        actual += timedelta(days=1)
    if not fechas:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "La repetición no incluye ningún día; revisa los días elegidos y la fecha de fin",
        )
    return fechas


# ---- Dietas ----

def validar_inicio_dieta(fecha_inicio: date, inicio_vigente: date | None) -> None:
    hoy = ahora().date()
    if fecha_inicio > hoy + timedelta(days=DIETA_INICIO_DIAS_FUTURO_MAX):
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Una dieta puede empezar como máximo {DIETA_INICIO_DIAS_FUTURO_MAX} días hacia adelante",
        )
    if inicio_vigente is not None and fecha_inicio <= inicio_vigente:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"La dieta nueva debe empezar después del inicio de la dieta vigente ({inicio_vigente.isoformat()})",
        )
