from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.logica_negocio.diagnostico_service import DiagnosticoService
from src.logica_negocio.utilidades import datos_a_actualizar
from src.modelos.fechas import hoy_local
from src.repositorios.tratamiento_repo import TratamientoRepository

CAMPOS_OBLIGATORIOS = {
    "descripcion",
    "frecuencia_valor",
    "frecuencia_unidad",
    "hora_inicio",
    "fecha_inicio",
    "estado",
}

def _validar_fechas(fecha_inicio, fecha_fin):
    if fecha_fin is not None and fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin no puede ser anterior a la fecha de inicio"
        )


def _validar_frecuencia(frecuencia_valor, frecuencia_unidad, hora_inicio):
    if (frecuencia_valor is None) != (frecuencia_unidad is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La frecuencia requiere valor y unidad",
        )
    if frecuencia_valor is not None and hora_inicio is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La frecuencia requiere hora de inicio",
        )


class TratamientoService:
    @staticmethod
    def _tratamiento_o_404(db: Session, id_tratamiento: int):
        tratamiento = TratamientoRepository.obtener_por_id(db, id_tratamiento)
        if not tratamiento:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tratamiento no encontrado")
        return tratamiento

    @staticmethod
    def listar_por_diagnostico(db: Session, id_diagnostico: int):
        DiagnosticoService.diagnostico_o_404(db, id_diagnostico)
        return TratamientoRepository.obtener_por_diagnostico(db, id_diagnostico)

    @staticmethod
    def crear_tratamiento(db: Session, id_diagnostico: int, tratamiento_in):
        DiagnosticoService.diagnostico_o_404(db, id_diagnostico)
        _validar_fechas(tratamiento_in.fecha_inicio or hoy_local(), tratamiento_in.fecha_fin)
        _validar_frecuencia(
            tratamiento_in.frecuencia_valor,
            tratamiento_in.frecuencia_unidad,
            tratamiento_in.hora_inicio,
        )
        datos = tratamiento_in.model_dump(exclude={"medicamentos"}, exclude_none=True)
        datos["id_diagnostico"] = id_diagnostico
        medicamentos = [medicamento.model_dump() for medicamento in tratamiento_in.medicamentos]
        return TratamientoRepository.crear_tratamiento(db, datos, medicamentos)

    @staticmethod
    def actualizar_tratamiento(db: Session, id_tratamiento: int, tratamiento_in):
        tratamiento = TratamientoService._tratamiento_o_404(db, id_tratamiento)
        datos = datos_a_actualizar(tratamiento_in, CAMPOS_OBLIGATORIOS)
        # Se valida con la combinación final: lo enviado y, si no se envió, lo que ya estaba guardado
        _validar_fechas(
            datos.get("fecha_inicio", tratamiento.fecha_inicio),
            datos.get("fecha_fin", tratamiento.fecha_fin),
        )
        _validar_frecuencia(
            datos.get("frecuencia_valor", tratamiento.frecuencia_valor),
            datos.get("frecuencia_unidad", tratamiento.frecuencia_unidad),
            datos.get("hora_inicio", tratamiento.hora_inicio),
        )
        if "medicamentos" in datos and datos["medicamentos"] is not None:
            datos["medicamentos"] = [
                medicamento.model_dump() for medicamento in datos["medicamentos"]
            ]
        return TratamientoRepository.actualizar_tratamiento(db, tratamiento, datos)
