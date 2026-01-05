# -*- coding: utf-8 -*-
"""
Configuración e inicialización de la base de datos PostgreSQL
"""
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from contextlib import contextmanager

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

# Base para los modelos
Base = declarative_base()

# Motor de base de datos
engine = None
Session = None

def get_engine():
    """Obtiene o crea el motor de base de datos"""
    global engine
    if engine is None:
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fungicloud')
        engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
    return engine

def get_session():
    """Obtiene la sesión de base de datos"""
    global Session
    if Session is None:
        engine = get_engine()
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)
    return Session()

@contextmanager
def get_db_session():
    """Context manager para sesiones de base de datos"""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error en transacción de base de datos: {e}")
        raise
    finally:
        session.close()

def init_database():
    """Inicializa la base de datos y crea las tablas"""
    try:
        engine = get_engine()
        
        # Importar todos los modelos
        from models.user import User
        from models.billing import UserBilling, BillingEvent
        from models.local_server import LocalServer
        from models.sync_data import SyncData, SyncEvent
        
        # Crear tablas
        Base.metadata.create_all(engine)
        logger.info("Base de datos inicializada correctamente")

        # Verificar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Conexión a base de datos verificada")

        # Inicializar registros de billing para cada usuario
        with get_db_session() as session:
            users = session.query(User).all()
            for user in users:
                billing = session.query(UserBilling).filter_by(user_id=user.id).first()
                if not billing:
                    # Admin obtiene plan expert (ilimitado), otros usuarios obtienen free
                    plan_type = 'expert' if user.is_admin else 'free'
                    billing = UserBilling(user_id=user.id, plan_type=plan_type, plan_status='active')
                    session.add(billing)
                    logger.info(f"Registro de billing creado para usuario {user.email} (id={user.id}, plan={plan_type})")
                elif user.is_admin and billing.plan_type == 'free':
                    # Actualizar admin que tenga plan free a expert
                    billing.plan_type = 'expert'
                    logger.info(f"Plan actualizado a 'expert' para admin {user.email} (id={user.id})")
            session.commit()
        
    except Exception as e:
        logger.error(f"Error al inicializar base de datos: {e}")
        raise

def reset_database():
    """Elimina y recrea todas las tablas (SOLO DESARROLLO)"""
    if os.getenv('FLASK_ENV') != 'development':
        raise Exception("reset_database() solo puede ejecutarse en modo desarrollo")
    
    engine = get_engine()
    Base.metadata.drop_all(engine)
    logger.warning("Todas las tablas eliminadas")
    
    init_database()
    logger.info("Base de datos reseteada")

if __name__ == '__main__':
    """Ejecutar para inicializar la base de datos"""
    print("\n" + "="*70)
    print("  🍄 FungiCloud - Inicialización de Base de Datos")
    print("="*70 + "\n")
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Verificar variables de entorno
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ Error: DATABASE_URL no configurada en .env")
            exit(1)
        
        print(f"📊 Conectando a: {database_url.split('@')[1] if '@' in database_url else database_url}")
        
        # Inicializar base de datos
        init_database()
        
        print("\n" + "="*70)
        print("  ✅ Base de datos inicializada correctamente")
        print("="*70)
        print("\n💡 Siguiente paso: python create_admin.py\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        exit(1)
