from flask import Flask
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv # <-- Nueva importación para cargar .env

#Configuración
from config import Config # Asumo que tienes un archivo config.py con tu clase Config
#blueprints
from routes.predict_routes import predict_bp
#bd
from database.models import db # <-- ¡Nueva importación!

def create_app():
    #Cargar las variables de entorno al inicio de la creación de la aplicación
    #Es una buena práctica cargarlas antes de acceder a Config, si Config las usa.
    load_dotenv()
    app = Flask(__name__)
    # Cargar configuración desde tu objeto Config
    app.config.from_object(Config)

    # Asegurar que la URL de PostgreSQL tenga el formato correcto
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace(
            "postgres://", "postgresql://", 1
        )

    #Configuración de CORS
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
    #Inicializa la base de datos con la aplicación
    db.init_app(app)
    #init_db(app)

    #Configuración de Logging (lo nuevo)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler('app.log', maxBytes=1024*1024*10,backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    #Crear las tablas de la base de datos si no existen
    #Esto reemplaza @app.before_request create_tables() si db.create_all() lo maneja.
    #Se requiere asegurar que database/models.py tenga db=SQLAlchemy()
    #y los modelos definidos con db.Model
    with app.app_context():
        #current_app.logger.info("Verificando y creando tablas de la base de datos...")
        db.create_all()
        #current_app.logger.info("Tablas de la base de datos verificadas/creadas")
    #Registrar los blueprints
    app.register_blueprint(predict_bp, url_prefix='/api')

    @app.route('/')
    def home():
        return "Backend para el predictor de cáncer de mama funcionando."
    
    return app

app = create_app()

if __name__ == '__main__':
    # Si quieres ejecutar localmente, asegúrate de que DATABASE_URL esté en tu .env.
    # Config.DEBUG y Config.FLASK_RUN_PORT seguirán funcionando como los tienes.
    app = create_app()
    with app.app_context():
        db.create_all()  # Crear tablas si no existen
    app.run(debug=Config.DEBUG, port=Config.FLASK_RUN_PORT)