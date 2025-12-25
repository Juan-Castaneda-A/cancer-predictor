import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cancer Predictor AI"
    API_V1_STR: str = "/api/v1"
    
    # Base de datos (Supabase)
    # Si no hay variable de entorno, usa una por defecto (útil para dev)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres.khrfshpinsvuxtcuzgit:Ryan17Wpro04$@aws-0-us-west-2.pooler.supabase.com:5432/postgres"
    )

    class Config:
        case_sensitive = True

settings = Settings()