from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.logica_negocio.diagnostico_service import DiagnosticoService
from src.logica_negocio.utilidades import datos_a_actualizar
from src.modelos.animal_model import hoy_local
from src.repositorios.tratamiento_repo import TratamientoRepository

CAMPOS_OBLIGATORIOS = {"medicamento_o_proceso", "fecha_inicio", "estado"}

def _validar_fechas(fecha_inicio, fecha_fin):
    if fecha_fin is not None and fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin no puede ser anterior a la fecha de inicio"
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
        # exclude_none: los campos no enviados toman su valor por defecto (ej. fecha de hoy)
        datos = tratamiento_in.model_dump(exclude_none=True)
        datos["id_diagnostico"] = id_diagnostico
        return TratamientoRepository.crear_tratamiento(db, datos)

    @staticmethod
    def actualizar_tratamiento(db: Session, id_tratamiento: int, tratamiento_in):
        tratamiento = TratamientoService._tratamiento_o_404(db, id_tratamiento)
        datos = datos_a_actualizar(tratamiento_in, CAMPOS_OBLIGATORIOS)
        # Se valida con la combinación final: lo enviado y, si no se envió, lo que ya estaba guardado
        _validar_fechas(
            datos.get("fecha_inicio", tratamiento.fecha_inicio),
            datos.get("fecha_fin", tratamiento.fecha_fin),
        )
        return TratamientoRepository.actualizar_tratamiento(db, tratamiento, datos)
