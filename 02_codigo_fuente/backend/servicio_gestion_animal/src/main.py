from fastapi import FastAPI
from src.api.routes import router as animales_router

app = FastAPI(title="Servicio de Gestión Animal - Yanacocha", version="1.0.0")

app.include_router(animales_router)

@app.get("/")
def root():
    return {"message": "Servicio de Gestión Animal operativo"}
