from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import CORS_ORIGINS
from src.proxy import crear_cliente_http
from src.rutas import accesos_router, actividades_router, gestion_animal_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Un único cliente HTTP compartido por todos los routers, cerrado al apagar el gateway
    async with crear_cliente_http() as cliente:
        app.state.http_client = cliente
        yield


app = FastAPI(title="API Gateway - Yanacocha", version="1.0.0", lifespan=lifespan)

# Permitimos que el frontend consuma el gateway desde el navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registramos las rutas del servicio de accesos de forma modular
app.include_router(accesos_router.router)
app.include_router(gestion_animal_router.router)
app.include_router(actividades_router.router)

# Liveness del propio gateway. Va directo en la app, fuera de los routers /api/*, así que no pasa por
# mapa_rutas ni por el proxy: no se agrega al mapa ni se reenvía a ningún servicio. No consulta a los
# servicios internos (si uno cae, el gateway sigue vivo y responde 503 en sus rutas).
@app.get("/health")
def liveness():
    return {"status": "ok"}

@app.get("/")
def health_check():
    return {"message": "API Gateway operando correctamente y listo para redirigir tráfico"}
