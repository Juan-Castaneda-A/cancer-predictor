from flask import Flask
from flask_cors import CORS
from config import Config # Asumo que tienes un archivo config.py con tu clase Config
from routes.predict_routes import predict_bp
import os
from database.models import create_tables # <-- ¡Nueva importación!
from dotenv import load_dotenv # <-- Nueva importación para cargar .env

# Carga las variables de entorno desde .env al inicio
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Modificamos CORS para que lea de la variable de entorno o use un default
# La URL de Render puede ser solo una, o varias separadas por coma.
# Si en Config.FRONTEND_URL tienes una URL fija, puedes mantenerla.
# Pero si quieres que sea flexible con Render y local, usar la variable de entorno es mejor.
# Aquí asumimos que FRONTEND_URL en tu Config es una cadena con las URLs separadas por coma.
# O podrías obtenerla directamente de os.getenv si la quieres desde .env o Render.
origins_list = Config.FRONTEND_URL.split(',') if isinstance(Config.FRONTEND_URL, str) else Config.FRONTEND_URL

CORS(app, resources={r"/api/*": {
    "origins": origins_list, # Usamos la lista de orígenes
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
}})

app.register_blueprint(predict_bp, url_prefix='/api')

# --- NUEVO: Hook para asegurar que las tablas de la DB se creen al iniciar la app ---
@app.before_request
def check_db_tables():
    # Esto se ejecutará ANTES de cada solicitud. Es un lugar conveniente
    # para asegurar que las tablas existan. SQLAlchemy es inteligente y no las recreará.
    # Es seguro llamarlo aquí.
    create_tables()

@app.route('/')
def home():
    return "Backend para el predictor de cáncer de mama funcionando."

if __name__ == '__main__':
    # Si quieres ejecutar localmente, asegúrate de que DATABASE_URL esté en tu .env.
    # Config.DEBUG y Config.FLASK_RUN_PORT seguirán funcionando como los tienes.
    app.run(debug=Config.DEBUG, port=Config.FLASK_RUN_PORT)