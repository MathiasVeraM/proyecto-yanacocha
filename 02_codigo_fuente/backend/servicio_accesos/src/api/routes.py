from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.esquemas.usuario_schema import UsuarioCreate, UsuarioResponse, UsuarioLogin, TokenResponse
from src.repositorios.usuario_repo import UsuarioRepository
from src.logica_negocio.auth import hash_password, verify_password, create_access_token, verificar_token_access

router = APIRouter(prefix="/api/auth", tags=["Autenticación y Usuarios"])

@router.post("/login", response_model=TokenResponse)
def login(form_data: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = UsuarioRepository.obtener_por_correo(db, form_data.correo)
    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Guardamos en el token el correo y el id_rol para verificarlo después
    token_data = {"sub": usuario.correo, "id_rol": usuario.id_rol}
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    usuario_in: UsuarioCreate, 
    db: Session = Depends(get_db),
    token_valido: dict = Depends(verificar_token_access)
):
    # VALIDACIÓN ESTRICTA: El id_rol 1 debe corresponder al Administrador
    # (Si el token no trae id_rol o es diferente de 1, se rechaza inmediatamente)
    if token_valido.get("id_rol") != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo los administradores pueden crear nuevas cuentas."
        )
    
    usuario_existente = UsuarioRepository.obtener_por_correo(db, usuario_in.correo)
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado"
        )
    
    hashed_pass = hash_password(usuario_in.password)
    datos_usuario = {
        "nombre": usuario_in.nombre,
        "apellido": usuario_in.apellido,
        "correo": usuario_in.correo,
        "password_hash": hashed_pass,
        "id_rol": usuario_in.id_rol
    }
    nuevo_usuario = UsuarioRepository.crear_usuario(db, datos_usuario)
    return nuevo_usuario