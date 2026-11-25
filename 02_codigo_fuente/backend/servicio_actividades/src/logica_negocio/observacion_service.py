from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.esquemas.observacion_schema import ObservacionCreate
from src.logica_negocio.actividad_service import ActividadService
from src.modelos.fechas import ahora_local
from src.repositorios.observacion_repo import ObservacionRepository

# Criterio de la HU RF-10: solo estas combinaciones generan alerta.
CATEGORIAS_CON_ALERTA = {"comportamiento", "estado_fisico"}
SEVERIDADES_CON_ALERTA = {"medio", "alto"}


class ObservacionService:
    @staticmethod
    def genera_alerta(categoria: str, severidad: str) -> bool:
        return categoria in CATEGORIAS_CON_ALERTA and severidad in SEVERIDADES_CON_ALERTA

    @staticmethod
    def crear(
        db: Session,
        id_actividad: int,
        datos: ObservacionCreate,
        id_usuario: int,
    ):
        ActividadService.actividad_o_404(db, id_actividad)
        return ObservacionRepository.crear(
            db,
            {
                "id_actividad": id_actividad,
                "categoria": datos.categoria,
                "severidad": datos.severidad,
                "detalle": datos.detalle,
                "genera_alerta": ObservacionService.genera_alerta(
                    datos.categoria,
                    datos.severidad,
                ),
                "id_usuario": id_usuario,
                "fecha_registro": ahora_local(),
            },
        )

    @staticmethod
    def listar_por_actividad(db: Session, id_actividad: int) -> list:
        ActividadService.actividad_o_404(db, id_actividad)
        return ObservacionRepository.listar_por_actividad(db, id_actividad)

    @staticmethod
    def listar_por_fechas(
        db: Session,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list:
        if fecha_desde is not None and fecha_hasta is not None and fecha_desde > fecha_hasta:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="fecha_desde no puede ser posterior a fecha_hasta",
            )
        return ObservacionRepository.listar_por_fechas(db, fecha_desde, fecha_hasta)
