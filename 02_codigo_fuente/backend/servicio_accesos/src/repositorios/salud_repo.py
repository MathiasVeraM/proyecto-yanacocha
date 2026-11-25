from sqlalchemy import text
from sqlalchemy.orm import Session


class SaludRepository:
    @staticmethod
    def consulta_trivial(db: Session) -> None:
        """Consulta que no toca ninguna tabla: solo comprueba que la base responde."""
        db.execute(text("SELECT 1"))
