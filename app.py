# -*- coding: utf-8 -*-
"""
FungiCloud - Servidor de Gestión Cloud
Gestiona usuarios, billing y sincronización de servidores locales
"""
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from database import init_database
from routes.auth_routes import auth_bp
from routes.billing_routes import billing_bp
from routes.sync_routes import sync_bp
from routes.admin_routes import admin_bp
from routes.alert_routes import alert_bp
from services.alert_service import start_alert_monitor

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear app Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fungicloud')

# CORS
CORS(app, resources={
    r"/api/*": {
        "origins": [os.getenv('FRONTEND_BASE_URL', 'http://localhost:4200')],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Registrar blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(billing_bp, url_prefix='/api')
app.register_blueprint(sync_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(alert_bp, url_prefix='/api')

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        "status": "healthy",
        "service": "FungiCloud",
        "version": "1.0.0"
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno del servidor: {error}")
    return jsonify({"success": False, "error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    # Inicializar base de datos
    logger.info("Inicializando base de datos...")
    init_database()
    
    # Iniciar monitor de alertas en segundo plano
    logger.info("Iniciando monitor de alertas...")
    start_alert_monitor()
    
    # Iniciar servidor
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Iniciando FungiCloud en puerto {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
