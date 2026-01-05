# -*- coding: utf-8 -*-
"""
Configuración e inicialización de la base de datos PostgreSQL
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

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
