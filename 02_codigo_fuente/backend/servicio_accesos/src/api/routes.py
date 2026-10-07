from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.esquemas.usuario_schema import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse, 
    UsuarioLogin, TokenResponse
)
from src.esquemas.rol_modulo_schema import RolCreate, ModuloCreate
from src.repositorios.usuario_repo import UsuarioRepository
from src.logica_negocio.auth import verify_password, create_access_token, verificar_es_admin
from src.logica_negocio.usuario_service import UsuarioService
from src.logica_negocio.rol_modulo_service import RolModuloService

router = APIRouter(prefix="/api/auth", tags=["Autenticación, Usuarios y Roles"])

@router.post("/login", response_model=TokenResponse)
def login(form_data: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = UsuarioRepository.obtener_por_correo(db, form_data.correo)
    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos"
        )
    access_token = create_access_token({"sub": usuario.correo, "id_rol": usuario.id_rol})
    return {"access_token": access_token, "token_type": "bearer"}

# --- RUTAS PROTEGIDAS EXCLUSIVAS PARA ADMINISTRADOR ---

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

# --- RUTAS DE CONSULTA PÚBLICAS O GENERALES (según necesites) ---

@router.get("/roles")
def listar_roles(db: Session = Depends(get_db)):
    return RolModuloService.listar_roles(db)

@router.get("/modulos")
def listar_modulos(db: Session = Depends(get_db)):
    return RolModuloService.listar_modulos(db)