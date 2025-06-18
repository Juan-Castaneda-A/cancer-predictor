from flask import Flask
from flask_cors import CORS
from config import Config
from routes.predict_routes import predict_bp # Asegúrate de que prediction_service.py esté en 'routes' y se llame 'predict_routes.py'
import os

app = Flask(__name__)
app.config.from_object(Config)

# Configurar CORS para permitir solicitudes desde el frontend
CORS(app, resources={r"/api/*": {
    "origins": Config.FRONTEND_URL,
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
}})

# Registrar Blueprints
app.register_blueprint(predict_bp, url_prefix='/api') # Esto conectará tus rutas de prediction_service.py bajo /api

@app.route('/')
def home():
    return "Backend para el predictor de cáncer de mama funcionando."

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, port=Config.FLASK_RUN_PORT)