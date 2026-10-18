# Registramos todos los modelos en el metadata de SQLAlchemy, porque usuario depende de la tabla rol (ForeignKey)
from src.modelos.rol_modulo_model import ModuloModel, RolModel, RolPermisoModel
from src.modelos.usuario_model import UsuarioModel

__all__ = ["ModuloModel", "RolModel", "RolPermisoModel", "UsuarioModel"]
