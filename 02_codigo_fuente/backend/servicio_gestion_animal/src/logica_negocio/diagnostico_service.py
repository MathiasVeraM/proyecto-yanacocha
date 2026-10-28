from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.logica_negocio.animal_service import AnimalService
from src.logica_negocio.utilidades import datos_a_actualizar
from src.repositorios.diagnostico_repo import DiagnosticoRepository

CAMPOS_OBLIGATORIOS = {"diagnostico", "es_critico"}

class DiagnosticoService:
    @staticmethod
    def diagnostico_o_404(db: Session, id_diagnostico: int):
        diagnostico = DiagnosticoRepository.obtener_por_id(db, id_diagnostico)
        if not diagnostico:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnóstico no encontrado")
        return diagnostico

    @staticmethod
    def listar_por_animal(db: Session, id_animal: int):
        AnimalService.animal_o_404(db, id_animal)
        return DiagnosticoRepository.obtener_por_animal(db, id_animal)

    @staticmethod
    def crear_diagnostico(db: Session, id_animal: int, id_usuario: int, diagnostico_in):
        AnimalService.animal_o_404(db, id_animal)
        datos = diagnostico_in.model_dump(exclude={"signos_vitales"})
        datos.update(id_animal=id_animal, id_usuario=id_usuario)
        signos_vitales = (
            diagnostico_in.signos_vitales.model_dump()
            if diagnostico_in.signos_vitales is not None
            else None
        )
        return DiagnosticoRepository.crear_diagnostico(db, datos, signos_vitales)

    @staticmethod
    def actualizar_diagnostico(db: Session, id_diagnostico: int, diagnostico_in):
        diagnostico = DiagnosticoService.diagnostico_o_404(db, id_diagnostico)
        datos = datos_a_actualizar(diagnostico_in, CAMPOS_OBLIGATORIOS)
        return DiagnosticoRepository.actualizar_diagnostico(db, diagnostico, datos)
