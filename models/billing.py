# -*- coding: utf-8 -*-
"""
Modelo de Billing para FungiCloud
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from database import Base

class UserBilling(Base):
    __tablename__ = 'user_billing'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Plan
    plan_type = Column(String(50), default='free', nullable=False)  # free, starter, advance, expert
    plan_status = Column(String(50), default='active', nullable=False)  # active, suspended, cancelled
    
    # Stripe
    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, index=True)
    
    # Período
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convierte a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_type': self.plan_type,
            'plan_status': self.plan_status,
            'stripe_customer_id': self.stripe_customer_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class BillingEvent(Base):
    __tablename__ = 'billing_events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)  # subscription_created, plan_changed, payment_succeeded, etc.
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        """Convierte a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
