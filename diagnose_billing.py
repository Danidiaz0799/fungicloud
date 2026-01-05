# -*- coding: utf-8 -*-
"""
Script de diagnóstico de billing
"""
import os
from dotenv import load_dotenv
load_dotenv()

from database import get_db_session
from models.user import User
from models.billing import UserBilling
from models.local_server import LocalServer

def diagnose():
    print("\n" + "="*70)
    print("  🔍 DIAGNÓSTICO DE BILLING")
    print("="*70 + "\n")
    
    with get_db_session() as session:
        # Verificar usuarios
        users = session.query(User).all()
        print(f"📊 Usuarios encontrados: {len(users)}\n")
        
        for user in users:
            print(f"👤 Usuario: {user.email} (ID: {user.id}, Admin: {user.is_admin})")
            
            # Billing
            billing = session.query(UserBilling).filter_by(user_id=user.id).first()
            if billing:
                print(f"   💳 Plan: {billing.plan_type} | Status: {billing.plan_status}")
            else:
                print(f"   ❌ Sin registro de billing")
            
            # Servidores locales
            servers = session.query(LocalServer).filter_by(user_id=user.id).all()
            print(f"   🖥️  Servidores registrados: {len(servers)}")
            for server in servers:
                print(f"      - {server.name} ({server.server_id}) - Status: {server.status}")
            
            print()
    
    print("="*70 + "\n")

if __name__ == '__main__':
    diagnose()
