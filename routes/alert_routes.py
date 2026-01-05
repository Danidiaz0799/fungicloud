# -*- coding: utf-8 -*-
"""
Rutas de Alertas para FungiCloud
"""
from flask import Blueprint, request, jsonify
from routes.auth_routes import verify_token
from database import get_db_session
from models.local_server import LocalServer
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
alert_bp = Blueprint('alert', __name__)

def require_auth():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, (jsonify({"success": False, "error": "Token requerido"}), 401)
    token = auth_header.replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return None, (jsonify({"success": False, "error": "Token inválido"}), 401)
    return payload, None

@alert_bp.route('/alerts/servers/offline', methods=['GET'])
def get_offline_servers():
    """Obtiene servidores offline del usuario"""
    user_data, error = require_auth()
    if error: return error
    
    threshold_minutes = int(request.args.get('threshold', 30))
    threshold = datetime.now() - timedelta(minutes=threshold_minutes)
    
    with get_db_session() as session:
        offline_servers = session.query(LocalServer).filter(
            LocalServer.user_id == user_data['user_id'],
            LocalServer.last_seen < threshold
        ).all()
        
        return jsonify({
            "success": True,
            "offline_servers": [server.to_dict() for server in offline_servers],
            "count": len(offline_servers),
            "threshold_minutes": threshold_minutes
        })

@alert_bp.route('/alerts/servers/<int:server_id>/settings', methods=['PUT'])
def update_alert_settings(server_id):
    """Actualiza configuración de alertas para un servidor"""
    user_data, error = require_auth()
    if error: return error
    
    data = request.get_json()
    
    with get_db_session() as session:
        server = session.query(LocalServer).filter_by(
            id=server_id,
            user_id=user_data['user_id']
        ).first()
        
        if not server:
            return jsonify({"success": False, "error": "Servidor no encontrado"}), 404
        
        if 'alerts_enabled' in data:
            server.alerts_enabled = data['alerts_enabled']
        if 'alert_email' in data:
            server.alert_email = data['alert_email']
        
        session.commit()
        return jsonify({"success": True, "server": server.to_dict()})
