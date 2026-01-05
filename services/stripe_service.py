# -*- coding: utf-8 -*-
"""
Servicio Stripe para FungiCloud (copia de raspServerNative)
"""
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe no instalado")

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
PLAN_PRICE_IDS = {
    'starter': os.getenv('STRIPE_STARTER_PRICE_ID', ''),
    'advance': os.getenv('STRIPE_ADVANCE_PRICE_ID', ''),
    'expert': os.getenv('STRIPE_EXPERT_PRICE_ID', '')
}

if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

class StripeService:
    def create_customer(self, email: str, user_id: int) -> Dict[str, Any]:
        try:
            customer = stripe.Customer.create(email=email, metadata={'user_id': str(user_id)})
            return {'success': True, 'customer_id': customer.id}
        except Exception as e:
            logger.error(f"Error Stripe: {e}")
            return {'success': False, 'message': str(e)}
    
    def create_checkout_session(self, customer_id: str, plan_type: str, user_id: int, success_url: str, cancel_url: str) -> Dict[str, Any]:
        try:
            price_id = PLAN_PRICE_IDS.get(plan_type)
            if not price_id:
                return {'success': False, 'message': 'Plan inválido'}
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={'user_id': str(user_id), 'plan_type': plan_type}
            )
            return {'success': True, 'checkout_url': session.url, 'session_id': session.id}
        except Exception as e:
            logger.error(f"Error checkout: {e}")
            return {'success': False, 'message': str(e)}
    
    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> Dict[str, Any]:
        try:
            if immediately:
                stripe.Subscription.delete(subscription_id)
            else:
                stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
            return {'success': True}
        except Exception as e:
            logger.error(f"Error cancelar: {e}")
            return {'success': False, 'message': str(e)}
    
    def verify_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        try:
            webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            return {'success': True, 'event': event}
        except Exception as e:
            logger.error(f"Error webhook: {e}")
            return {'success': False, 'message': str(e)}
