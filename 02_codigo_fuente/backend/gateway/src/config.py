import os
from dotenv import load_dotenv

load_dotenv()

# URL del microservicio de accesos
ACCESSOS_SERVICE_URL = os.getenv("ACCESSOS_SERVICE_URL", "http://localhost:8001")

# Clave con la que accesos firma los tokens. Sin valor por defecto: si falta, el gateway no arranca. 
# Debe ser igual a la del servicio de accesos en los .env.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Falta la variable de entorno SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Orígenes permitidos para CORS (separados por coma)
CORS_ORIGINS = [
    origen.strip()
    for origen in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origen.strip()
]

# Tiempo máximo (en segundos) que el gateway espera la respuesta de un servicio
PROXY_TIMEOUT_SECONDS = float(os.getenv("PROXY_TIMEOUT_SECONDS", "10"))
