# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from routes.auth_routes import verify_token
from database import get_db_session
from models.user import User
from models.billing import UserBilling
from models.local_server import LocalServer
from models.sync_data import SyncData
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

def require_admin():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, (jsonify({"success": False, "error": "Token requerido"}), 401)
    token = auth_header.replace('Bearer ', '')
    payload = verify_token(token)
    if not payload or not payload.get('is_admin'):
        return None, (jsonify({"success": False, "error": "Acceso denegado"}), 403)
    return payload, None

@admin_bp.route('/admin/dashboard', methods=['GET'])
def get_dashboard():
    user_data, error = require_admin()
    if error: return error
    
    with get_db_session() as session:
        total_users = session.query(User).filter_by(is_active=True).count()
        users_by_plan = session.query(
            UserBilling.plan_type,
            func.count(UserBilling.id)
        ).group_by(UserBilling.plan_type).all()
        
        plan_stats = {plan: count for plan, count in users_by_plan}
        
        # Total de servidores locales
        total_servers = session.query(LocalServer).count()
        servers_online = session.query(LocalServer).filter_by(status='online').count()
        
        # Total de cultivos (clientes)
        total_clients = session.query(func.sum(LocalServer.clients_count)).scalar() or 0
        clients_online = session.query(func.sum(LocalServer.clients_online)).scalar() or 0
        
        # Ingresos mensuales (MRR - Monthly Recurring Revenue)
        mrr = 0
        for plan, count in users_by_plan:
            plan_prices = {'free': 0, 'starter': 5.00, 'advance': 17.50, 'expert': 29.50}
            mrr += count * plan_prices.get(plan, 0)
        
        # Últimas sincronizaciones
        recent_syncs = session.query(SyncData).order_by(desc(SyncData.received_at)).limit(10).all()
        
        # Servidores con problemas (offline > 30 min)
        threshold = datetime.now() - timedelta(minutes=30)
        offline_servers = session.query(LocalServer).filter(
            LocalServer.last_seen < threshold
        ).all()
        
        dashboard_data = {
            'users': {
                'total': total_users,
                'by_plan': plan_stats,
                'free': plan_stats.get('free', 0),
                'starter': plan_stats.get('starter', 0),
                'advance': plan_stats.get('advance', 0),
                'expert': plan_stats.get('expert', 0)
            },
            'servers': {
                'total': total_servers,
                'online': servers_online,
                'offline': total_servers - servers_online
            },
            'clients': {
                'total': total_clients,
                'online': clients_online,
                'offline': total_clients - clients_online
            },
            'revenue': {
                'mrr': round(mrr, 2),
                'currency': 'USD'
            },
            'recent_syncs': [sync.to_dict() for sync in recent_syncs],
            'offline_servers': [server.to_dict() for server in offline_servers]
        }
        
        return jsonify({"success": True, "dashboard": dashboard_data})

@admin_bp.route('/admin/users', methods=['GET'])
def list_all_users():
    """Lista todos los usuarios con su información de billing"""
    user_data, error = require_admin()
    if error: return error
    
    with get_db_session() as session:
        users = session.query(User).all()
        users_data = []
        
        for user in users:
            billing = session.query(UserBilling).filter_by(user_id=user.id).first()
            servers = session.query(LocalServer).filter_by(user_id=user.id).all()
            
            users_data.append({
                **user.to_dict(),
                'billing': billing.to_dict() if billing else None,
                'servers_count': len(servers),
                'servers_online': sum(1 for s in servers if s.is_online())
            })
        
        return jsonify({"success": True, "users": users_data, "count": len(users_data)})

@admin_bp.route('/admin/users/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    """Detalles completos de un usuario específico"""
    admin_data, error = require_admin()
    if error: return error
    
    with get_db_session() as session:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        
        billing = session.query(UserBilling).filter_by(user_id=user.id).first()
        servers = session.query(LocalServer).filter_by(user_id=user.id).all()
        
        return jsonify({
            "success": True,
            "user": user.to_dict(),
            "billing": billing.to_dict() if billing else None,
            "servers": [server.to_dict() for server in servers]
        })

@admin_bp.route('/admin/users/<int:user_id>/suspend', methods=['POST'])
def suspend_user(user_id):
    """Suspende un usuario"""
    admin_data, error = require_admin()
    if error: return error
    
    with get_db_session() as session:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        
        user.is_active = False
        session.commit()
        
        logger.warning(f"Usuario {user.email} suspendido por admin {admin_data['email']}")
        return jsonify({"success": True, "message": "Usuario suspendido"})

@admin_bp.route('/admin/servers', methods=['GET'])
def list_all_servers():
    """Lista todos los servidores locales de todos los usuarios"""
    admin_data, error = require_admin()
    if error: return error
    
    with get_db_session() as session:
        servers = session.query(LocalServer).all()
        return jsonify({
            "success": True,
            "servers": [server.to_dict() for server in servers],
            "count": len(servers)
        })
