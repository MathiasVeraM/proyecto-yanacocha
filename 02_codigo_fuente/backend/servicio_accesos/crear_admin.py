from src.database import SessionLocal
from src.modelos.usuario_model import UsuarioModel
from src.logica_negocio.auth import hash_password

db = SessionLocal()

# Verifica si ya existe para no duplicarlo
correo_admin = "admin.principal@yanacocha.com"
existente = db.query(UsuarioModel).filter(UsuarioModel.correo == correo_admin).first()

if not existente:
    nuevo_admin = UsuarioModel(
        nombre="Administrador",
        apellido="Sistema",
        correo=correo_admin,
        password_hash=hash_password("AdminSecure2026*"),
        id_rol=1, # Asegúrate de que el id 1 sea tu rol Administrador en la BD
        activo=True
    )
    db.add(nuevo_admin)
    db.commit()
    print(f"¡Administrador creado con éxito! Correo: {correo_admin} | Contraseña: AdminSecure2026*")
else:
    print("El administrador ya existe en la base de datos.")

db.close()