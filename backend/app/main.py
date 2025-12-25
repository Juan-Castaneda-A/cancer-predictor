from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="API Científica para predicción de crecimiento tumoral usando SciPy y Supabase."
)

# Configuración de CORS (Permitir conexiones desde React)
origins = [
    "http://localhost:5173",  # Puerto por defecto de Vite (React)
    "http://localhost:3000",
    "*" # ⚠️ En producción cambia esto por tu dominio real
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Cancer Predictor V2 API - Online 🟢"}