class Config:
    # URL para el frontend (útil para CORS si no usas CORS(app) sin restricciones)
    FRONTEND_URL = "https://cancer-frontend.onrender.com" # O la URL de tu frontend si usas Live Server u otro puerto
    # Puerto del backend
    FLASK_RUN_PORT = 5000
    # Desactivar modo debug en producción
    DEBUG = True # CÁMBIALO A False PARA PRODUCCIÓN
    TESTING = False