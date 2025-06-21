from flask import Flask
from flask_cors import CORS
from config import Config
from routes.predict_routes import predict_bp
import os

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {
    "origins": Config.FRONTEND_URL,
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
}})

app.register_blueprint(predict_bp, url_prefix='/api')

@app.route('/')
def home():
    return "Backend para el predictor de cáncer de mama funcionando."

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, port=Config.FLASK_RUN_PORT)