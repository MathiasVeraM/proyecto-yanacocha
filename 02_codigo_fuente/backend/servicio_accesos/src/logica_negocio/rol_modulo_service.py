from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositorios.rol_modulo_repo import RolModuloRepository

ID_ROL_ADMIN = 1


def _datos_a_actualizar(esquema, campos_obligatorios):
    """Campos enviados por el cliente; los obligatorios no aceptan null."""
    datos = esquema.model_dump(exclude_unset=True)
    return {k: v for k, v in datos.items() if v is not None or k not in campos_obligatorios}


class RolModuloService:
    @staticmethod
    def _rol_o_404(db: Session, id_rol: int):
        rol = RolModuloRepository.obtener_rol_por_id(db, id_rol)
        if not rol:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
        return rol

    @staticmethod
    def _modulo_o_404(db: Session, id_modulo: int):
        modulo = RolModuloRepository.obtener_modulo_por_id(db, id_modulo)
        if not modulo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
        return modulo

    @staticmethod
    def listar_roles(db: Session):
        return RolModuloRepository.obtener_roles(db)

    @staticmethod
    def crear_rol(db: Session, rol_in):
        if RolModuloRepository.obtener_rol_por_nombre(db, rol_in.nombre_rol):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un rol con ese nombre"
            )
        return RolModuloRepository.crear_rol(db, rol_in.model_dump())

    @staticmethod
    def listar_modulos(db: Session):
        return RolModuloRepository.obtener_modulos(db)

    @staticmethod
    def crear_modulo(db: Session, modulo_in):
        if RolModuloRepository.obtener_modulo_por_nombre(db, modulo_in.nombre_modulo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un módulo con ese nombre"
            )
        return RolModuloRepository.crear_modulo(db, modulo_in.model_dump())

    @staticmethod
    def actualizar_rol(db: Session, id_rol: int, rol_in):
        rol = RolModuloService._rol_o_404(db, id_rol)
        datos = _datos_a_actualizar(rol_in, {"nombre_rol"})
        nombre = datos.get("nombre_rol")
        if nombre and nombre != rol.nombre_rol and RolModuloRepository.obtener_rol_por_nombre(db, nombre):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un rol con ese nombre"
            )
        return RolModuloRepository.actualizar_rol(db, rol, datos)

    @staticmethod
    def eliminar_rol(db: Session, id_rol: int):
        rol = RolModuloService._rol_o_404(db, id_rol)
        if rol.id_rol == ID_ROL_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El rol de Administrador no se puede eliminar"
            )
        if RolModuloRepository.contar_usuarios_por_rol(db, id_rol) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El rol tiene usuarios asignados; reasígnalos antes de eliminarlo"
            )
        RolModuloRepository.eliminar_permisos_de_rol(db, id_rol)
        RolModuloRepository.eliminar_rol(db, rol)

    @staticmethod
    def actualizar_modulo(db: Session, id_modulo: int, modulo_in):
        modulo = RolModuloService._modulo_o_404(db, id_modulo)
        datos = _datos_a_actualizar(modulo_in, {"nombre_modulo", "codigo_servicio"})
        nombre = datos.get("nombre_modulo")
        if nombre and nombre != modulo.nombre_modulo and RolModuloRepository.obtener_modulo_por_nombre(db, nombre):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un módulo con ese nombre"
            )
        return RolModuloRepository.actualizar_modulo(db, modulo, datos)

    @staticmethod
    def eliminar_modulo(db: Session, id_modulo: int):
        modulo = RolModuloService._modulo_o_404(db, id_modulo)
        RolModuloRepository.eliminar_permisos_de_modulo(db, id_modulo)
        RolModuloRepository.eliminar_modulo(db, modulo)

    @staticmethod
    def asignar_permiso(db: Session, id_rol: int, id_modulo: int):
        RolModuloService._rol_o_404(db, id_rol)
        RolModuloService._modulo_o_404(db, id_modulo)
        if not RolModuloRepository.existe_permiso(db, id_rol, id_modulo):
            RolModuloRepository.asignar_permiso(db, id_rol, id_modulo)
        return {"id_rol": id_rol, "id_modulo": id_modulo}

    @staticmethod
    def quitar_permiso(db: Session, id_rol: int, id_modulo: int):
        RolModuloService._rol_o_404(db, id_rol)
        RolModuloService._modulo_o_404(db, id_modulo)
        if id_rol == ID_ROL_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se pueden quitar permisos al rol de Administrador"
            )
        RolModuloRepository.quitar_permiso(db, id_rol, id_modulo)

    @staticmethod
    def obtener_matriz(db: Session):
        roles = sorted(RolModuloRepository.obtener_roles(db), key=lambda r: r.id_rol)
        modulos = sorted(RolModuloRepository.obtener_modulos(db), key=lambda m: m.id_modulo)
        permisos = sorted(RolModuloRepository.obtener_permisos(db), key=lambda p: (p.id_rol, p.id_modulo))
        return {
            "roles": [
                {
                    "id_rol": r.id_rol,
                    "nombre_rol": r.nombre_rol,
                    "descripcion": r.descripcion,
                    "total_usuarios": RolModuloRepository.contar_usuarios_por_rol(db, r.id_rol),
                }
                for r in roles
            ],
            "modulos": [
                {"id_modulo": m.id_modulo, "nombre_modulo": m.nombre_modulo, "codigo_servicio": m.codigo_servicio}
                for m in modulos
            ],
            "permisos": [{"id_rol": p.id_rol, "id_modulo": p.id_modulo} for p in permisos],
        }
