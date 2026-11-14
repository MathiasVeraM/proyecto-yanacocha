from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.esquemas.dieta_schema import DietaCreate
from src.logica_negocio import reglas_actividad as reglas
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
        # No antes del inicio de la dieta vigente y con un límite hacia el futuro
        vigente = DietaRepository.obtener_vigente(db, datos.id_animal)
        reglas.validar_inicio_dieta(datos.fecha_inicio, vigente.fecha_inicio if vigente else None)
        dieta_data = datos.model_dump(exclude={"alimentos"})
        dieta_data.update(
            id_usuario_creador=id_usuario,
            vigente=True,
        )
        alimentos = [alimento.model_dump() for alimento in datos.alimentos]
        return DietaRepository.crear_dieta(db, dieta_data, alimentos)

    @staticmethod
    def _vigente_o_409(db: Session, id_dieta: int):
        dieta = DietaService.dieta_o_404(db, id_dieta)
        if not dieta.vigente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La dieta ya no está vigente",
            )
        return dieta

    @staticmethod
    def finalizar(db: Session, id_dieta: int):
        """Termina la dieta hoy: guarda la fecha de fin y quita las tomas pendientes desde mañana."""
        dieta = DietaService._vigente_o_409(db, id_dieta)
        hoy = reglas.ahora().date()
        return DietaRepository.cambiar_fin(db, dieta, max(dieta.fecha_inicio, hoy), vigente=False)

    @staticmethod
    def cambiar_fin(db: Session, id_dieta: int, fecha_fin, id_usuario: int):
        """Pone, extiende o quita la fecha de fin de la dieta vigente y ajusta sus tomas."""
        dieta = DietaService._vigente_o_409(db, id_dieta)
        hoy = reglas.ahora().date()
        if fecha_fin is not None and fecha_fin < max(dieta.fecha_inicio, hoy):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La fecha de fin no puede ser anterior a hoy ni al inicio de la dieta; "
                "para terminarla hoy usa Finalizar",
            )
        dieta = DietaRepository.cambiar_fin(db, dieta, fecha_fin, vigente=True)
        # Si se extendió (o se quitó el fin), se generan las tomas que falten dentro del horizonte
        from src.logica_negocio.actividad_service import ActividadService

        ActividadService.generar_tomas(db, dieta.id_dieta, id_usuario)
        return dieta

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
