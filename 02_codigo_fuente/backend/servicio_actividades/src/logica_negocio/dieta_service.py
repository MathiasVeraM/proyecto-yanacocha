from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.esquemas.dieta_schema import DietaCreate
from src.repositorios.dieta_repo import DietaRepository
from src.repositorios.referencias_repo import ReferenciasRepository


class DietaService:
    @staticmethod
    def _validar_dieta(datos: DietaCreate) -> None:
        if (
            datos.frecuencia_valor <= 0
            or datos.frecuencia_valor > 2147483647
            or datos.frecuencia_unidad
            not in {
                "horas",
                "dias",
                "semanas",
            }
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La frecuencia de la dieta no es válida",
            )
        if not datos.alimentos:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La dieta requiere al menos un alimento",
            )
        if datos.fecha_fin is not None and datos.fecha_fin < datos.fecha_inicio:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="fecha_fin debe ser igual o posterior a fecha_inicio",
            )
        for alimento in datos.alimentos:
            if not alimento.nombre_alimento.strip() or alimento.cantidad_gramos <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cada alimento requiere nombre y cantidad positiva",
                )

    @staticmethod
    def dieta_o_404(db: Session, id_dieta: int):
        dieta = DietaRepository.obtener_por_id(db, id_dieta)
        if dieta is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dieta no encontrada",
            )
        return dieta

    @staticmethod
    def crear_dieta(db: Session, id_usuario: int, datos: DietaCreate):
        DietaService._validar_dieta(datos)
        if not ReferenciasRepository.existe_animal(db, datos.id_animal):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Animal no encontrado",
            )
        dieta_data = datos.model_dump(exclude={"alimentos"})
        dieta_data.update(
            id_usuario_creador=id_usuario,
            vigente=True,
        )
        alimentos = [alimento.model_dump() for alimento in datos.alimentos]
        return DietaRepository.crear_dieta(db, dieta_data, alimentos)

    @staticmethod
    def listar_todas(db: Session):
        return DietaRepository.obtener_todas(db)

    @staticmethod
    def listar_por_animal(db: Session, id_animal: int):
        if not ReferenciasRepository.existe_animal(db, id_animal):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Animal no encontrado",
            )
        return DietaRepository.obtener_por_animal(db, id_animal)

    @staticmethod
    def vigente_por_animal(db: Session, id_animal: int):
        if not ReferenciasRepository.existe_animal(db, id_animal):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Animal no encontrado",
            )
        dieta = DietaRepository.obtener_vigente(db, id_animal)
        if dieta is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dieta vigente no encontrada",
            )
        return dieta
