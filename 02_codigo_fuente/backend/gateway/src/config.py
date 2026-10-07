import os
from dotenv import load_dotenv

load_dotenv()

# URL del microservicio de accesos
ACCESSOS_SERVICE_URL = os.getenv("ACCESSOS_SERVICE_URL", "http://localhost:8001")