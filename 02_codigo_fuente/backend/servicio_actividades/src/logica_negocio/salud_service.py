import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from src.repositorios.salud_repo import SaludRepository

logger = logging.getLogger(__name__)


class SaludService:
    @staticmethod
    def base_de_datos_disponible(db: Session) -> bool:
        try:
            SaludRepository.consulta_trivial(db)
        except SQLAlchemyError as error:
            # Solo se registra el tipo de error: el detalle puede incluir datos de conexión
            logger.warning("La base de datos no respondió: %s", type(error).__name__)
            return False
        return True
