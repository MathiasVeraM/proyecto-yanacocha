from sqlalchemy.orm import Session

from src.logica_negocio.animal_service import AnimalService
from src.repositorios.diagnostico_repo import DiagnosticoRepository


class SignosVitalesService:
    @staticmethod
    def listar_por_animal(db: Session, id_animal: int):
        AnimalService.animal_o_404(db, id_animal)
        return DiagnosticoRepository.obtener_signos_vitales_por_animal(db, id_animal)
