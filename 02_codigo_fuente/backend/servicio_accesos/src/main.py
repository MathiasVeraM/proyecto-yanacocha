from fastapi import FastAPI
from src.api.routes import router as auth_router

app = FastAPI(title="Servicio de Accesos - Yanacocha", version="1.0.0")

app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Servicio de Accesos operativo"}