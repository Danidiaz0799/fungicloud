# -*- coding: utf-8 -*-
"""
Script para limpiar servidores duplicados y corregir billing
"""
import os
from dotenv import load_dotenv
load_dotenv()

from database import get_db_session
from models.user import User
from models.billing import UserBilling
from models.local_server import LocalServer
from models.sync_data import SyncData, SyncEvent

def cleanup():
    print("\n" + "="*70)
    print("  🧹 LIMPIEZA Y CORRECCIÓN")
    print("="*70 + "\n")
    
    with get_db_session() as session:
        # 1. Corregir planes de billing
        print("📋 Corrigiendo planes de billing...\n")
        users = session.query(User).all()
        for user in users:
            correct_plan = 'expert' if user.is_admin else 'free'
            billing = session.query(UserBilling).filter_by(user_id=user.id).first()
            
            if billing and billing.plan_type != correct_plan:
                old_plan = billing.plan_type
                billing.plan_type = correct_plan
                print(f"✅ {user.email}: {old_plan} → {correct_plan}")
        
        # 2. Eliminar servidores duplicados (mantener el más reciente)
        print("\n🖥️  Limpiando servidores duplicados...\n")
        users = session.query(User).all()
        for user in users:
            servers = session.query(LocalServer).filter_by(user_id=user.id).order_by(LocalServer.id.desc()).all()
            
            if len(servers) > 1:
                print(f"👤 Usuario: {user.email}")
                print(f"   Servidores encontrados: {len(servers)}")
                
                # Mantener el primero (más reciente), eliminar el resto
                keep = servers[0]
                to_delete = servers[1:]
                
                print(f"   ✓ Manteniendo: {keep.name} (ID: {keep.server_id})")
                for server in to_delete:
                    print(f"   ❌ Eliminando: {server.name} (ID: {server.server_id})")
                    
                    # Primero eliminar eventos de sincronización
                    sync_events = session.query(SyncEvent).filter_by(server_id=server.id).all()
                    if sync_events:
                        print(f"      - Eliminando {len(sync_events)} eventos de sync")
                        for se in sync_events:
                            session.delete(se)
                    session.flush()  # Forzar eliminación antes de continuar
                    
                    # Luego eliminar datos de sincronización
                    sync_data = session.query(SyncData).filter_by(server_id=server.id).all()
                    if sync_data:
                        print(f"      - Eliminando {len(sync_data)} registros de sync_data")
                        for sd in sync_data:
                            session.delete(sd)
                    session.flush()  # Forzar eliminación antes de continuar
                    
                    # Ahora sí eliminar el servidor
                    session.delete(server)
                    session.flush()  # Forzar eliminación del servidor
        
        session.commit()
        print("\n✅ Limpieza completada\n")
    
    print("="*70 + "\n")

if __name__ == '__main__':
    cleanup()
