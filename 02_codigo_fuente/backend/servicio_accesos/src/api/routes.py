from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.esquemas.usuario_schema import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse,
    UsuarioLogin, TokenResponse
)
from src.esquemas.rol_modulo_schema import RolCreate, RolUpdate, ModuloCreate, ModuloUpdate
from src.logica_negocio.auth import verificar_es_admin
from src.logica_negocio.auth_service import AuthService
from src.logica_negocio.usuario_service import UsuarioService
from src.logica_negocio.rol_modulo_service import RolModuloService

router = APIRouter(prefix="/api/auth", tags=["Autenticación, Usuarios y Roles"])

@router.post("/login", response_model=TokenResponse)
def login(form_data: UsuarioLogin, db: Session = Depends(get_db)):
    access_token = AuthService.iniciar_sesion(db, form_data.correo, form_data.password)
    return {"access_token": access_token, "token_type": "bearer"}

# --- RUTAS PROTEGIDAS EXCLUSIVAS PARA ADMINISTRADOR ---

@router.get("/usuarios", response_model=List[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    return UsuarioService.listar_usuarios(db)

@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario_in: UsuarioCreate, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    return UsuarioService.crear_nuevo_usuario(db, usuario_in)

@router.put("/usuarios/{id_usuario}", response_model=UsuarioResponse)
def actualizar_usuario(id_usuario: int, usuario_in: UsuarioUpdate, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    return UsuarioService.actualizar_datos_usuario(db, id_usuario, usuario_in)

@router.patch("/usuarios/{id_usuario}/desactivar", response_model=UsuarioResponse)
def desactivar_usuario(id_usuario: int, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    return UsuarioService.desactivar_usuario(db, id_usuario)

@router.post("/roles", status_code=status.HTTP_201_CREATED)
def crear_rol(rol_in: RolCreate, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    return RolModuloService.crear_rol(db, rol_in)

@router.post("/modulos", status_code=status.HTTP_201_CREATED)
def crear_modulo(modulo_in: ModuloCreate, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    return RolModuloService.crear_modulo(db, modulo_in)

@router.put("/roles/{id_rol}")
def actualizar_rol(id_rol: int, rol_in: RolUpdate, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    return RolModuloService.actualizar_rol(db, id_rol, rol_in)

@router.delete("/roles/{id_rol}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_rol(id_rol: int, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    RolModuloService.eliminar_rol(db, id_rol)

@router.put("/modulos/{id_modulo}")
def actualizar_modulo(id_modulo: int, modulo_in: ModuloUpdate, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    return RolModuloService.actualizar_modulo(db, id_modulo, modulo_in)

@router.delete("/modulos/{id_modulo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_modulo(id_modulo: int, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    RolModuloService.eliminar_modulo(db, id_modulo)

@router.get("/permisos/matriz")
def obtener_matriz_permisos(db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    return RolModuloService.obtener_matriz(db)

@router.put("/permisos/{id_rol}/{id_modulo}")
def asignar_permiso(id_rol: int, id_modulo: int, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    return RolModuloService.asignar_permiso(db, id_rol, id_modulo)

@router.delete("/permisos/{id_rol}/{id_modulo}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_permiso(id_rol: int, id_modulo: int, db: Session = Depends(get_db), _: dict = Depends(verificar_es_admin)):
    RolModuloService.quitar_permiso(db, id_rol, id_modulo)

# --- RUTAS DE CONSULTA PÚBLICAS O GENERALES (según necesites) ---

@router.get("/roles")
def listar_roles(db: Session = Depends(get_db)):
    return RolModuloService.listar_roles(db)

@router.get("/modulos")
def listar_modulos(db: Session = Depends(get_db)):
    return RolModuloService.listar_modulos(db)