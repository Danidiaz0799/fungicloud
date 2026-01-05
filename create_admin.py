#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear usuario administrador inicial
"""
import sys
import getpass
from database import get_db_session, init_database
from models.user import User

def create_admin_user():
    """Crea un usuario administrador"""
    print("=" * 50)
    print("Crear Usuario Administrador - FungiCloud")
    print("=" * 50)
    
    # Inicializar DB
    print("\n[1/5] Inicializando base de datos...")
    init_database()
    
    # Solicitar datos
    print("\n[2/5] Datos del administrador:")
    email = input("Email: ").strip()
    
    if not email or '@' not in email:
        print("❌ Email inválido")
        sys.exit(1)
    
    password = getpass.getpass("Contraseña: ")
    password_confirm = getpass.getpass("Confirmar contraseña: ")
    
    if password != password_confirm:
        print("❌ Las contraseñas no coinciden")
        sys.exit(1)
    
    if len(password) < 8:
        print("❌ La contraseña debe tener al menos 8 caracteres")
        sys.exit(1)
    
    # Verificar si ya existe
    print("\n[3/5] Verificando si el usuario ya existe...")
    with get_db_session() as session:
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            print(f"❌ Ya existe un usuario con email {email}")
            sys.exit(1)
    
    # Crear usuario
    print("\n[4/5] Creando usuario administrador...")
    with get_db_session() as session:
        admin = User(
            email=email,
            is_active=True,
            is_admin=True
        )
        admin.set_password(password)
        session.add(admin)
        session.commit()
        admin_id = admin.id
    
    # Confirmar
    print("\n[5/5] ✅ Usuario administrador creado exitosamente!")
    print(f"\n📧 Email: {email}")
    print(f"🆔 ID: {admin_id}")
    print(f"👑 Admin: Sí")
    print("\nPuedes iniciar sesión en /api/auth/login")
    print("=" * 50)

if __name__ == '__main__':
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
