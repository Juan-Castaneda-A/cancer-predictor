from sqlmodel import SQLModel
from app.db.session import engine
# Importamos los modelos para registrar sus metadatos antes de crear las tablas
from app.models import Patient, TumorMeasurement

def init_db():
    print("⏳ Creando tablas en Supabase...")
    # Esta línea mágica crea todas las tablas definidas en los modelos importados
    SQLModel.metadata.create_all(engine)
    print("✅ ¡Tablas creadas exitosamente!")

if __name__ == "__main__":
    init_db()