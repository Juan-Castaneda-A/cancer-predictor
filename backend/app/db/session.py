# app/db/session.py
from sqlmodel import create_engine, Session
from app.core.config import settings

# Supabase requiere pool_pre_ping=True para mantener conexiones estables
engine = create_engine(settings.DATABASE_URL, echo=True, pool_pre_ping=True)

def get_session():
    """Dependency para inyectar la sesión en los endpoints"""
    with Session(engine) as session:
        yield session