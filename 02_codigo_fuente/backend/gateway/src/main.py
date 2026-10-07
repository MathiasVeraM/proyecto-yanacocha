from fastapi import FastAPI
from src.rutas import accesos_router

app = FastAPI(title="API Gateway - Yanacocha", version="1.0.0")

# Registramos las rutas del servicio de accesos de forma modular
app.include_router(accesos_router.router)

@app.get("/")
def health_check():
    return {"message": "API Gateway operando correctamente y listo para redirigir tráfico"}