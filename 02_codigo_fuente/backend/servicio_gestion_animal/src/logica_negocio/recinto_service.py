from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.logica_negocio.utilidades import datos_a_actualizar
from src.repositorios.recinto_repo import RecintoRepository

CAMPOS_OBLIGATORIOS = {"nombre_recinto", "estado"}

def _nombre_repetido():
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Ya existe un recinto con ese nombre"
    )

class RecintoService:
    @staticmethod
    def recinto_o_404(db: Session, id_recinto: int):
        recinto = RecintoRepository.obtener_por_id(db, id_recinto)
        if not recinto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recinto no encontrado")
        return recinto

    @staticmethod
    def listar_recintos(db: Session):
        return RecintoRepository.obtener_todos(db)

    @staticmethod
    def crear_recinto(db: Session, recinto_in):
        if RecintoRepository.obtener_por_nombre(db, recinto_in.nombre_recinto):
            raise _nombre_repetido()
        return RecintoRepository.crear_recinto(db, recinto_in.model_dump())

    @staticmethod
    def actualizar_recinto(db: Session, id_recinto: int, recinto_in):
        recinto = RecintoService.recinto_o_404(db, id_recinto)
        datos = datos_a_actualizar(recinto_in, CAMPOS_OBLIGATORIOS)
        nombre = datos.get("nombre_recinto")
        if nombre and nombre != recinto.nombre_recinto and RecintoRepository.obtener_por_nombre(db, nombre):
            raise _nombre_repetido()
        return RecintoRepository.actualizar_recinto(db, recinto, datos)
