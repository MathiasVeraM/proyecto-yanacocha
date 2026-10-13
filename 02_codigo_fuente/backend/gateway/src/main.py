from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import CORS_ORIGINS
from src.rutas import accesos_router

app = FastAPI(title="API Gateway - Yanacocha", version="1.0.0")

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

@app.get("/")
def health_check():
    return {"message": "API Gateway operando correctamente y listo para redirigir tráfico"}