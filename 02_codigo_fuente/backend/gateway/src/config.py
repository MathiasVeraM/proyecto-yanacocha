import os
from dotenv import load_dotenv

load_dotenv()

# URL del microservicio de accesos
ACCESSOS_SERVICE_URL = os.getenv("ACCESSOS_SERVICE_URL", "http://localhost:8001")

# Orígenes permitidos para CORS (separados por coma)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")