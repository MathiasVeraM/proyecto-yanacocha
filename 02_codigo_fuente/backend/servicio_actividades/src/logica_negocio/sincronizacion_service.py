from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.esquemas.observacion_schema import ObservacionCreate
from src.esquemas.sincronizacion_schema import (
    CompletadaSync,
    ObservacionSync,
    ResultadoItemSync,
    SincronizacionRequest,
)
from src.logica_negocio.actividad_service import ActividadService
from src.logica_negocio.observacion_service import ObservacionService
from src.repositorios.observacion_repo import ObservacionRepository


def _detalle(error: HTTPException) -> str:
    return error.detail if isinstance(error.detail, str) else str(error.detail)


class SincronizacionService:
    """Recibe lo registrado sin conexión. Cada registro se resuelve por separado:

    - es idempotente (reenviar el mismo lote no duplica nada);
    - un registro inválido no impide guardar los demás;
    - conflictos: la actividad ya completada conserva a quien la completó primero y la
      actividad borrada se rechaza (la app descarta el registro en ambos casos).
    """

    @staticmethod
    def sincronizar(db: Session, datos: SincronizacionRequest, id_usuario: int) -> dict:
        return {
            "completadas": [
                SincronizacionService._completada(db, item, id_usuario)
                for item in datos.completadas
            ],
            "observaciones": [
                SincronizacionService._observacion(db, item, id_usuario)
                for item in datos.observaciones
            ],
        }

    @staticmethod
    def _completada(db: Session, item: CompletadaSync, id_usuario: int) -> ResultadoItemSync:
        try:
            ActividadService.completar(
                db,
                item.id_actividad,
                id_usuario,
                item.observaciones,
                True,
                item.fecha_completada,
            )
        except HTTPException as error:
            if error.status_code == status.HTTP_409_CONFLICT and "ya está completada" in _detalle(error):
                return ResultadoItemSync(
                    id_actividad=item.id_actividad,
                    resultado="duplicada",
                    detalle="La actividad ya estaba completada",
                )
            return ResultadoItemSync(
                id_actividad=item.id_actividad,
                resultado="rechazada",
                detalle=_detalle(error),
            )
        return ResultadoItemSync(id_actividad=item.id_actividad, resultado="creada")

    @staticmethod
    def _observacion(db: Session, item: ObservacionSync, id_usuario: int) -> ResultadoItemSync:
        try:
            if ObservacionRepository.obtener_por_id_cliente(db, item.id_cliente) is not None:
                return ResultadoItemSync(
                    id_actividad=item.id_actividad,
                    id_cliente=item.id_cliente,
                    resultado="duplicada",
                )
            ObservacionService.crear(
                db,
                item.id_actividad,
                ObservacionCreate(
                    categoria=item.categoria,
                    severidad=item.severidad,
                    detalle=item.detalle,
                    id_cliente=item.id_cliente,
                    fecha_registro=item.fecha_registro,
                ),
                id_usuario,
            )
        except HTTPException as error:
            return ResultadoItemSync(
                id_actividad=item.id_actividad,
                id_cliente=item.id_cliente,
                resultado="rechazada",
                detalle=_detalle(error),
            )
        return ResultadoItemSync(
            id_actividad=item.id_actividad,
            id_cliente=item.id_cliente,
            resultado="creada",
        )
