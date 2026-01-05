# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from routes.auth_routes import verify_token
from database import get_db_session
from models.local_server import LocalServer
from models.sync_data import SyncData, SyncEvent
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
sync_bp = Blueprint('sync', __name__)

def require_auth():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, (jsonify({"success": False, "error": "Token requerido"}), 401)
    token = auth_header.replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return None, (jsonify({"success": False, "error": "Token inválido"}), 401)
    return payload, None

@sync_bp.route('/sync/register', methods=['POST'])
def register_server():
    """Registra un nuevo servidor local"""
    user_data, error = require_auth()
    if error: return error
    
    data = request.get_json()
    server_id = data.get('server_id')
    name = data.get('name', 'Servidor Local')
    
    if not server_id:
        return jsonify({"success": False, "error": "server_id requerido"}), 400
    
    with get_db_session() as session:
        server = session.query(LocalServer).filter_by(server_id=server_id).first()
        
        if server:
            server.last_seen = datetime.now()
            server.status = 'online'
        else:
            server = LocalServer(
                user_id=user_data['user_id'],
                server_id=server_id,
                name=name,
                status='online',
                last_seen=datetime.now()
            )
            session.add(server)
        
        session.commit()
        logger.info(f"Servidor registrado: {server_id} para usuario {user_data['user_id']}")
        return jsonify({"success": True, "server": server.to_dict()})

@sync_bp.route('/sync/data', methods=['POST'])
def sync_data():
    """Recibe datos sincronizados de un servidor local"""
    user_data, error = require_auth()
    if error: return error
    
    data = request.get_json()
    server_id = data.get('server_id')
    
    if not server_id:
        return jsonify({"success": False, "error": "server_id requerido"}), 400
    
    with get_db_session() as session:
        server = session.query(LocalServer).filter_by(
            server_id=server_id,
            user_id=user_data['user_id']
        ).first()
        
        if not server:
            return jsonify({"success": False, "error": "Servidor no registrado"}), 404
        
        # Actualizar estado del servidor
        server.last_seen = datetime.now()
        server.last_sync_at = datetime.now()
        server.status = 'online'
        server.clients_count = data.get('clients_total', 0)
        server.clients_online = data.get('clients_online', 0)
        server.version = data.get('version', '1.0.0')
        server.ip_address = data.get('ip_address', request.remote_addr)
        
        # Guardar datos sincronizados
        sync_data_obj = SyncData(
            server_id=server.id,
            user_id=user_data['user_id'],
            data_timestamp=datetime.now(),
            avg_temperature=data.get('avg_temperature', 0),
            min_temperature=data.get('min_temperature', 0),
            max_temperature=data.get('max_temperature', 0),
            avg_humidity=data.get('avg_humidity', 0),
            min_humidity=data.get('min_humidity', 0),
            max_humidity=data.get('max_humidity', 0),
            avg_light_intensity=data.get('avg_light_intensity', 0),
            avg_pressure=data.get('avg_pressure', 0),
            clients_total=data.get('clients_total', 0),
            clients_online=data.get('clients_online', 0),
            readings_count=data.get('readings_count', 0)
        )
        session.add(sync_data_obj)
        
        # Registrar evento de sync exitoso
        event = SyncEvent(
            server_id=server.id,
            event_type='sync_success',
            message=f'Sincronización exitosa - {data.get("readings_count", 0)} lecturas'
        )
        session.add(event)
        
        session.commit()
        logger.info(f"Datos sincronizados de servidor {server_id}")
        return jsonify({"success": True, "message": "Datos sincronizados"})

@sync_bp.route('/sync/servers', methods=['GET'])
def list_servers():
    """Lista los servidores locales del usuario"""
    user_data, error = require_auth()
    if error: return error
    
    with get_db_session() as session:
        servers = session.query(LocalServer).filter_by(user_id=user_data['user_id']).all()
        return jsonify({
            "success": True,
            "servers": [server.to_dict() for server in servers]
        })
