from datetime import date, datetime, time, timedelta
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.config import HORIZONTE_TOMAS_DIAS
from src.database import Base
from src.esquemas.actividad_schema import ActividadBaseCreate
from src.modelos.actividad_alimentacion_model import ActividadAlimentacionModel
from src.modelos.actividad_enriquecimiento_model import ActividadEnriquecimientoModel
from src.modelos.actividad_entrenamiento_model import ActividadEntrenamientoModel
from src.modelos.actividad_tratamiento_model import ActividadTratamientoModel
from src.modelos.fechas import ahora_local, hoy_local
from src.repositorios.actividad_repo import ActividadRepository
from src.repositorios.dieta_repo import DietaRepository
from src.repositorios.referencias_repo import ReferenciasRepository


HORIZONTE_TRATAMIENTOS_DIAS = 7


class ActividadService:
    @staticmethod
    def _validar_datos(tipo: str, datos: dict) -> None:
        tipos_validos = {
            "alimentacion",
            "enriquecimiento",
            "entrenamiento",
            "limpieza",
        }
        if tipo not in tipos_validos:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tipo de actividad no válido",
            )

        horas = datos.get("duracion_horas", 0)
        minutos = datos.get("duracion_minutos", 0)
        if horas < 0 or horas > 32767 or minutos < 0 or minutos > 59:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La duración de la actividad no es válida",
            )
        duracion_total = horas * 60 + minutos
        if tipo == "limpieza":
            if datos.get("id_recinto") is None or datos.get("id_animal") is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="La limpieza requiere recinto y no puede asociarse a un animal",
                )
            if duracion_total <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="La limpieza requiere duración mayor que cero",
                )
            return

        if datos.get("id_animal") is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La actividad requiere id_animal",
            )
        if tipo == "entrenamiento":
            if (
                duracion_total <= 0
                or datos.get("hora_programada") is None
                or not str(datos.get("objetivo_entrenamiento", "")).strip()
                or not str(datos.get("tipo_refuerzo", "")).strip()
                or len(str(datos.get("tipo_refuerzo", ""))) > 150
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="El entrenamiento requiere objetivo, refuerzo, hora y duración positiva",
                )
        elif tipo == "enriquecimiento":
            if (
                datos.get("hora_programada") is None
                or datos.get("tipo_enriquecimiento")
                not in {"social", "sensorial", "alimenticio", "cognitivo"}
                or not str(datos.get("descripcion_estimulo", "")).strip()
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="El enriquecimiento requiere tipo, estímulo y hora válidos",
                )
        elif datos.get("id_dieta") is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La alimentación requiere id_dieta",
            )

    @staticmethod
    def _verificar_referencias(db: Session, tipo: str, datos: dict) -> None:
        if tipo == "limpieza":
            if not ReferenciasRepository.existe_recinto(db, datos["id_recinto"]):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recinto no encontrado",
                )
            return

        if not ReferenciasRepository.existe_animal(db, datos["id_animal"]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Animal no encontrado",
            )
        if tipo == "alimentacion":
            dieta = DietaRepository.obtener_por_id(db, datos["id_dieta"])
            if dieta is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dieta no encontrada",
                )
            if dieta.id_animal != datos["id_animal"]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="La dieta no pertenece al animal indicado",
                )

    @staticmethod
    def crear(
        db: Session,
        tipo: str,
        datos: dict,
        id_usuario: int,
    ):
        ActividadService._validar_datos(tipo, datos)
        ActividadService._verificar_referencias(db, tipo, datos)
        detalle = None
        if tipo == "alimentacion":
            detalle = {"_modelo": ActividadAlimentacionModel, "id_dieta": datos.pop("id_dieta")}
        elif tipo == "enriquecimiento":
            detalle = {
                "_modelo": ActividadEnriquecimientoModel,
                "tipo_enriquecimiento": datos.pop("tipo_enriquecimiento"),
                "descripcion_estimulo": datos.pop("descripcion_estimulo"),
            }
        elif tipo == "entrenamiento":
            detalle = {
                "_modelo": ActividadEntrenamientoModel,
                "objetivo_entrenamiento": datos.pop("objetivo_entrenamiento"),
                "tipo_refuerzo": datos.pop("tipo_refuerzo"),
            }

        datos["tipo_actividad"] = tipo
        datos["id_usuario_programo"] = id_usuario
        datos["completada"] = False
        datos["id_usuario_completo"] = None
        datos["fecha_completada"] = None
        return ActividadRepository.crear(db, datos, detalle)

    @staticmethod
    def crear_desde_esquema(
        db: Session,
        datos: ActividadBaseCreate,
        id_usuario: int,
    ):
        return ActividadService.crear(
            db,
            datos.tipo_actividad,
            datos.model_dump(exclude={"tipo_actividad"}, exclude_none=True),
            id_usuario,
        )

    @staticmethod
    def actividad_o_404(db: Session, id_actividad: int):
        actividad = ActividadRepository.obtener_por_id(db, id_actividad)
        if actividad is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Actividad no encontrada",
            )
        return actividad

    @staticmethod
    def listar(
        db: Session,
        id_animal: int | None = None,
        id_recinto: int | None = None,
        tipo_actividad: str | None = None,
        completada: bool | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ):
        if fecha_desde is not None and fecha_hasta is not None and fecha_desde > fecha_hasta:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="fecha_desde no puede ser posterior a fecha_hasta",
            )
        if tipo_actividad not in {
            None,
            "alimentacion",
            "enriquecimiento",
            "entrenamiento",
            "limpieza",
            "tratamiento",
        }:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tipo de actividad no válido",
            )
        return ActividadRepository.listar(
            db,
            id_animal,
            id_recinto,
            tipo_actividad,
            completada,
            fecha_desde,
            fecha_hasta,
        )

    @staticmethod
    def completar(
        db: Session,
        id_actividad: int,
        id_usuario: int,
        observaciones: str | None,
        actualizar_observaciones: bool = True,
    ):
        actividad = ActividadService.actividad_o_404(db, id_actividad)
        if actividad.completada:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La actividad ya está completada",
            )
        return ActividadRepository.completar(
            db,
            actividad,
            id_usuario,
            observaciones,
            actualizar_observaciones,
            ahora_local(),
        )

    @staticmethod
    def reabrir(db: Session, id_actividad: int):
        actividad = ActividadService.actividad_o_404(db, id_actividad)
        if not actividad.completada:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La actividad no está completada",
            )
        return ActividadRepository.reabrir(db, actividad)

    @staticmethod
    def generar_tomas(
        db: Session,
        id_dieta: int,
        id_usuario: int,
        fecha_hasta: date | None = None,
    ) -> list:
        dieta = DietaRepository.obtener_por_id(db, id_dieta)
        if dieta is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dieta no encontrada",
            )

        hoy = hoy_local()
        fecha_inicio = dieta.fecha_inicio
        if fecha_hasta is None or fecha_hasta >= hoy:
            fecha_inicio = max(fecha_inicio, hoy)
        horizonte_fin = fecha_inicio + timedelta(days=HORIZONTE_TOMAS_DIAS - 1)
        fecha_limite = min(fecha_hasta or horizonte_fin, horizonte_fin)
        if dieta.fecha_fin is not None:
            fecha_limite = min(fecha_limite, dieta.fecha_fin)
        if fecha_limite < fecha_inicio:
            return []

        horarios = ActividadService._horarios_tomas(
            dieta.fecha_inicio,
            fecha_inicio,
            fecha_limite,
            dieta.frecuencia_valor,
            dieta.frecuencia_unidad,
        )
        # Las tomas que ya existen se traen de una vez y se buscan en memoria
        existentes = {
            (toma.fecha_programada, toma.hora_programada): toma
            for toma in ActividadRepository.listar_tomas_rango(
                db, dieta.id_dieta, fecha_inicio, fecha_limite
            )
        }
        resultado = []
        for fecha, hora in horarios:
            toma = existentes.get((fecha, hora))
            if toma is None:
                toma = ActividadService.crear(
                    db,
                    "alimentacion",
                    {
                        "id_animal": dieta.id_animal,
                        "id_dieta": dieta.id_dieta,
                        "fecha_programada": fecha,
                        "hora_programada": hora,
                        "duracion_horas": 0,
                        "duracion_minutos": 0,
                        "observaciones": None,
                    },
                    id_usuario,
                )
            resultado.append(toma)
        return resultado

    @staticmethod
    def renovar_horizonte(db: Session, id_usuario: int) -> list:
        dietas = DietaRepository.listar_vigentes(db)
        return [
            toma
            for dieta in dietas
            for toma in ActividadService.generar_tomas(
                db,
                dieta.id_dieta,
                id_usuario,
                hoy_local() + timedelta(days=HORIZONTE_TOMAS_DIAS - 1),
            )
        ]

    @staticmethod
    def generar_tratamiento(db: Session, id_tratamiento: int, id_usuario: int) -> list:
        tabla_tratamiento = Base.metadata.tables["gestion_animal.tratamiento"]
        tabla_diagnostico = Base.metadata.tables["gestion_animal.diagnostico"]
        consulta = (
            select(
                tabla_tratamiento.c.id_tratamiento,
                tabla_tratamiento.c.fecha_inicio,
                tabla_tratamiento.c.fecha_fin,
                tabla_tratamiento.c.frecuencia_valor,
                tabla_tratamiento.c.frecuencia_unidad,
                tabla_tratamiento.c.hora_inicio,
                tabla_tratamiento.c.estado,
                tabla_diagnostico.c.id_animal,
            )
            .select_from(
                tabla_tratamiento.join(
                    tabla_diagnostico,
                    tabla_diagnostico.c.id_diagnostico
                    == tabla_tratamiento.c.id_diagnostico,
                )
            )
            .where(tabla_tratamiento.c.id_tratamiento == id_tratamiento)
        )
        tratamiento = db.execute(consulta).mappings().first()
        if tratamiento is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tratamiento no encontrado",
            )
        if (
            tratamiento["frecuencia_valor"] is None
            or tratamiento["frecuencia_unidad"] is None
            or tratamiento["hora_inicio"] is None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El tratamiento requiere frecuencia y hora de inicio para generar actividades",
            )

        ahora = ahora_local()
        horarios = (
            ActividadService._horarios_tratamiento(
                tratamiento["fecha_inicio"],
                tratamiento["fecha_fin"],
                tratamiento["hora_inicio"],
                tratamiento["frecuencia_valor"],
                tratamiento["frecuencia_unidad"],
                ahora,
            )
            if tratamiento["estado"] == "en_curso"
            else []
        )
        horarios_esperados = set(horarios)

        existentes = ActividadRepository.obtener_actividades_tratamiento(
            db, id_tratamiento
        )
        # Las dosis que se conservan se buscan en memoria, sin una consulta por horario
        conservadas = {}
        for actividad in existentes:
            detalle = actividad.tratamiento
            programacion = (
                detalle.fecha_programada,
                detalle.hora_programada,
            )
            instante = datetime.combine(*programacion)
            if (
                not actividad.completada
                and instante > ahora
                and programacion not in horarios_esperados
            ):
                ActividadRepository.eliminar_actividad_tratamiento(db, actividad)
            else:
                conservadas[programacion] = actividad

        resultado = []
        for fecha, hora in horarios:
            actividad = conservadas.get((fecha, hora))
            if actividad is None:
                try:
                    actividad = ActividadRepository.crear(
                        db,
                        {
                            "tipo_actividad": "tratamiento",
                            "id_animal": tratamiento["id_animal"],
                            "fecha_programada": fecha,
                            "hora_programada": hora,
                            "duracion_horas": 0,
                            "duracion_minutos": 0,
                            "id_usuario_programo": id_usuario,
                            "completada": False,
                            "observaciones": "Dosis programada de tratamiento",
                            "id_usuario_completo": None,
                            "fecha_completada": None,
                        },
                        {
                            "_modelo": ActividadTratamientoModel,
                            "id_tratamiento": id_tratamiento,
                            "fecha_programada": fecha,
                            "hora_programada": hora,
                        },
                    )
                except IntegrityError:
                    actividad = ActividadRepository.obtener_actividad_tratamiento(
                        db, id_tratamiento, fecha, hora
                    )
                    if actividad is None:
                        raise
            resultado.append(actividad)
        return resultado

    @staticmethod
    def renovar_horizonte_tratamientos(db: Session, id_usuario: int) -> list:
        tabla_tratamiento = Base.metadata.tables["gestion_animal.tratamiento"]
        ids = db.execute(
            select(tabla_tratamiento.c.id_tratamiento).where(
                tabla_tratamiento.c.estado == "en_curso",
                tabla_tratamiento.c.frecuencia_valor.is_not(None),
                tabla_tratamiento.c.frecuencia_unidad.is_not(None),
                tabla_tratamiento.c.hora_inicio.is_not(None),
            )
        ).scalars().all()
        return [
            actividad
            for id_tratamiento in ids
            for actividad in ActividadService.generar_tratamiento(
                db, id_tratamiento, id_usuario
            )
        ]

    @staticmethod
    def _horarios_tratamiento(
        fecha_inicio: date,
        fecha_fin: date | None,
        hora_inicio: time,
        frecuencia_valor: int,
        frecuencia_unidad: str,
        ahora: datetime,
    ) -> list[tuple[date, time]]:
        hoy = ahora.date()
        fecha_limite = hoy + timedelta(days=HORIZONTE_TRATAMIENTOS_DIAS - 1)
        if fecha_fin is not None:
            fecha_limite = min(fecha_limite, fecha_fin)
        if fecha_limite < max(fecha_inicio, hoy):
            return []

        primer_instante = datetime.combine(fecha_inicio, hora_inicio)
        inicio_horizonte = max(ahora, datetime.combine(hoy, time.min))
        fin_horizonte = datetime.combine(fecha_limite, time.max)
        paso_segundos = frecuencia_valor * (
            60 * 60 if frecuencia_unidad == "horas" else 24 * 60 * 60
        )
        if primer_instante < inicio_horizonte:
            segundos_hasta_inicio = (inicio_horizonte - primer_instante).total_seconds()
            saltos = ceil(segundos_hasta_inicio / paso_segundos)
            desplazamiento = saltos * paso_segundos
            if desplazamiento > (fin_horizonte - primer_instante).total_seconds():
                return []
            primer_instante += timedelta(seconds=desplazamiento)
        if primer_instante > fin_horizonte:
            return []

        horarios = []
        instante = primer_instante
        while instante <= fin_horizonte:
            if instante >= inicio_horizonte:
                horarios.append((instante.date(), instante.time()))
            if paso_segundos > (fin_horizonte - instante).total_seconds():
                break
            instante += timedelta(seconds=paso_segundos)
        return horarios

    @staticmethod
    def _horarios_tomas(
        inicio: date,
        fecha_generacion: date,
        limite: date,
        frecuencia_valor: int,
        frecuencia_unidad: str,
    ) -> list[tuple[date, time]]:
        if frecuencia_unidad in {"dias", "semanas"}:
            paso_dias = frecuencia_valor * (7 if frecuencia_unidad == "semanas" else 1)
            dias_transcurridos = (fecha_generacion - inicio).days
            saltos = (dias_transcurridos + paso_dias - 1) // paso_dias
            desplazamiento = saltos * paso_dias
            if desplazamiento > (limite - inicio).days:
                return []
            fecha = inicio + timedelta(days=desplazamiento)
            horarios = []
            while fecha <= limite:
                horarios.append((fecha, time(8, 0)))
                if paso_dias > (limite - fecha).days:
                    break
                fecha += timedelta(days=paso_dias)
            return horarios

        primer_instante = datetime.combine(inicio, time(8, 0))
        desde = datetime.combine(fecha_generacion, time.min)
        hasta = datetime.combine(limite, time(23, 59, 59))
        paso_segundos = frecuencia_valor * 60 * 60
        segundos_transcurridos = max(0, (desde - primer_instante).total_seconds())
        saltos = int((segundos_transcurridos + paso_segundos - 1) // paso_segundos)
        desplazamiento = saltos * paso_segundos
        if desplazamiento > (hasta - primer_instante).total_seconds():
            return []
        actual = primer_instante + timedelta(seconds=desplazamiento)
        horarios = []
        while actual <= hasta:
            horarios.append((actual.date(), actual.time()))
            if paso_segundos > (hasta - actual).total_seconds():
                break
            actual += timedelta(seconds=paso_segundos)
        return horarios

    @staticmethod
    def calendario(actividades: list) -> list[dict]:
        eventos = []
        for actividad in actividades:
            todo_el_dia = actividad.hora_programada is None
            if todo_el_dia:
                inicio = actividad.fecha_programada.isoformat()
                fin = inicio
            else:
                comienzo = datetime.combine(actividad.fecha_programada, actividad.hora_programada)
                fin_datetime = comienzo + timedelta(
                    hours=actividad.duracion_horas,
                    minutes=actividad.duracion_minutos,
                )
                inicio = comienzo.isoformat()
                fin = fin_datetime.isoformat()
            eventos.append(
                {
                    "id_actividad": actividad.id_actividad,
                    "inicio": inicio,
                    "fin": fin,
                    "tipo": actividad.tipo_actividad,
                    "completada": actividad.completada,
                    "todo_el_dia": todo_el_dia,
                }
            )
        return eventos
