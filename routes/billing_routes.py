# -*- coding: utf-8 -*-
"""
Rutas de Billing para FungiCloud
"""
from flask import Blueprint, request, jsonify
from routes.auth_routes import verify_token
from database import get_db_session
from models.user import User
from models.billing import UserBilling, BillingEvent
from services.stripe_service import StripeService
import logging
import os

logger = logging.getLogger(__name__)
billing_bp = Blueprint('billing', __name__)

PLAN_LIMITS = {'free': 1, 'starter': 3, 'advance': 10, 'expert': -1}
PLAN_PRICES = {'free': 0, 'starter': 5.00, 'advance': 17.50, 'expert': 29.50}

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
        return jsonify({"success": True, "billing": billing.to_dict()})

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
