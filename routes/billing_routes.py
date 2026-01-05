# -*- coding: utf-8 -*-
"""
Rutas de Billing para FungiCloud
"""
from flask import Blueprint, request, jsonify
from routes.auth_routes import verify_token
from database import get_db_session
from models.user import User
from models.billing import UserBilling, BillingEvent
from models.local_server import LocalServer
from services.stripe_service import StripeService
import logging
import os

logger = logging.getLogger(__name__)
billing_bp = Blueprint('billing', __name__)

PLAN_LIMITS = {'free': 1, 'starter': 3, 'advance': 10, 'expert': -1}
PLAN_PRICES = {'free': 0, 'starter': 5.00, 'advance': 17.50, 'expert': 29.50}
PLAN_DISPLAY_NAMES = {'free': 'Gratis', 'starter': 'Starter', 'advance': 'Advance', 'expert': 'Expert'}

def require_auth():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, (jsonify({"success": False, "error": "Token requerido"}), 401)
    token = auth_header.replace('Bearer ', '')
    payload = verify_token(token)
    if not payload:
        return None, (jsonify({"success": False, "error": "Token inválido"}), 401)
    return payload, None

@billing_bp.route('/billing/status', methods=['GET'])
def get_billing_status():
    user_data, error = require_auth()
    if error: return error
    
    with get_db_session() as session:
        billing = session.query(UserBilling).filter_by(user_id=user_data['user_id']).first()
        if not billing:
            return jsonify({"success": False, "error": "Billing no encontrado"}), 404
        
        # Contar servidores locales (clientes) del usuario
        clients_count = session.query(LocalServer).filter_by(user_id=user_data['user_id']).count()
        
        # Obtener límite según el plan
        plan_limit = PLAN_LIMITS.get(billing.plan_type, 1)
        can_create = True if plan_limit == -1 else clients_count < plan_limit
        
        # Construir respuesta con billing completo
        billing_data = billing.to_dict()
        billing_data['plan_display_name'] = PLAN_DISPLAY_NAMES.get(billing.plan_type, billing.plan_type.capitalize())
        billing_data['limits'] = {
            'clients': {
                'current': clients_count,
                'limit': plan_limit,
                'can_create': can_create
            }
        }
        
        return jsonify({"success": True, "billing": billing_data})

@billing_bp.route('/billing/plans', methods=['GET'])
def get_plans():
    plans = [
        {'type': 'free', 'display_name': 'Gratis', 'price': 0, 'limits': {'clients': 1}, 'features': ['1 cultivo']},
        {'type': 'starter', 'display_name': 'Starter', 'price': 5.00, 'limits': {'clients': 3}, 'features': ['3 cultivos', 'Automatización básica']},
        {'type': 'advance', 'display_name': 'Advance', 'price': 17.50, 'limits': {'clients': 10}, 'features': ['10 cultivos', 'Automatización avanzada']},
        {'type': 'expert', 'display_name': 'Expert', 'price': 29.50, 'limits': {'clients': -1}, 'features': ['Ilimitado', 'API access']}
    ]
    return jsonify({"success": True, "plans": plans})

@billing_bp.route('/billing/checkout/create', methods=['POST'])
def create_checkout():
    user_data, error = require_auth()
    if error: return error
    
    data = request.get_json()
    plan_type = data.get('plan_type')
    
    if plan_type not in ['starter', 'advance', 'expert']:
        return jsonify({"success": False, "error": "Plan inválido"}), 400
    
    stripe_service = StripeService()
    base_url = os.getenv('FRONTEND_BASE_URL', 'http://localhost:4200')
    
    with get_db_session() as session:
        user = session.query(User).filter_by(id=user_data['user_id']).first()
        billing = session.query(UserBilling).filter_by(user_id=user.id).first()
        
        customer_id = billing.stripe_customer_id
        if not customer_id:
            result = stripe_service.create_customer(user.email, user.id)
            if not result['success']:
                return jsonify({"success": False, "error": "Error creando cliente"}), 500
            customer_id = result['customer_id']
            billing.stripe_customer_id = customer_id
            session.commit()
        
        result = stripe_service.create_checkout_session(
            customer_id, plan_type, user.id,
            f"{base_url}/billing/checkout/success",
            f"{base_url}/billing/checkout/cancel"
        )
        
        if result['success']:
            return jsonify({"success": True, "checkout_url": result['checkout_url']})
        return jsonify({"success": False, "error": result['message']}), 500

@billing_bp.route('/billing/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    # Implementar lógica de webhook de Stripe
    return jsonify({"success": True})

@billing_bp.route('/billing/subscription/cancel', methods=['POST'])
def cancel_subscription():
    """Cancela la suscripción del usuario"""
    user_data, error = require_auth()
    if error: return error
    
    data = request.get_json()
    immediately = data.get('immediately', False)
    
    with get_db_session() as session:
        billing = session.query(UserBilling).filter_by(user_id=user_data['user_id']).first()
        
        if not billing or not billing.stripe_subscription_id:
            return jsonify({"success": False, "error": "No hay suscripción activa"}), 404
        
        stripe_service = StripeService()
        result = stripe_service.cancel_subscription(billing.stripe_subscription_id, immediately)
        
        if result['success']:
            if immediately:
                billing.plan_type = 'free'
                billing.plan_status = 'cancelled'
                billing.stripe_subscription_id = None
            else:
                billing.plan_status = 'cancelling'
            
            # Registrar evento
            event = BillingEvent(
                user_id=user_data['user_id'],
                event_type='subscription_cancelled',
                event_metadata={'immediately': immediately}
            )
            session.add(event)
            session.commit()
            
            return jsonify({
                "success": True,
                "message": "Suscripción cancelada" if immediately else "Suscripción se cancelará al final del período"
            })
        
        return jsonify({"success": False, "error": result.get('message', 'Error desconocido')}), 500

@billing_bp.route('/billing/events', methods=['GET'])
def get_billing_events():
    """Obtiene el historial de eventos de billing del usuario"""
    user_data, error = require_auth()
    if error: return error
    
    limit = request.args.get('limit', 50, type=int)
    event_type = request.args.get('event_type', None)
    
    with get_db_session() as session:
        query = session.query(BillingEvent).filter_by(user_id=user_data['user_id'])
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        events = query.order_by(BillingEvent.created_at.desc()).limit(limit).all()
        
        return jsonify({
            "success": True,
            "events": [e.to_dict() for e in events],
            "count": len(events)
        })

