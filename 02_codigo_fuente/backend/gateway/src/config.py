import os
from dotenv import load_dotenv

load_dotenv()

# URL del microservicio de accesos
ACCESSOS_SERVICE_URL = os.getenv("ACCESSOS_SERVICE_URL", "http://localhost:8001")

# Orígenes permitidos para CORS (separados por coma)
CORS_ORIGINS = [
    origen.strip()
    for origen in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origen.strip()
]

# Tiempo máximo (en segundos) que el gateway espera la respuesta de un servicio
PROXY_TIMEOUT_SECONDS = float(os.getenv("PROXY_TIMEOUT_SECONDS", "10"))
