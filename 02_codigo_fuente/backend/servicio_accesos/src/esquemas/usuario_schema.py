from typing import Optional
from pydantic import BaseModel, EmailStr

class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str
    correo: EmailStr
    password: str
    id_rol: int

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    correo: Optional[EmailStr] = None
    password: Optional[str] = None
    id_rol: Optional[int] = None
    activo: Optional[bool] = None

class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre: str
    apellido: str
    correo: EmailStr
    id_rol: int
    activo: bool

    class Config:
        from_attributes = True

class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"