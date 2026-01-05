# -*- coding: utf-8 -*-
"""
Modelo de Servidor Local para FungiCloud
Representa cada instancia de raspServerNative que los usuarios tienen en su LAN
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base

class LocalServer(Base):
    __tablename__ = 'local_servers'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Identificación
    server_id = Column(String(255), unique=True, nullable=False, index=True)  # ID único del servidor local
    name = Column(String(255), nullable=False)  # Nombre amigable (ej: "Casa Principal", "Granja Norte")
    description = Column(Text)
    
    # Estado
    status = Column(String(50), default='offline', nullable=False)  # online, offline, error
    last_seen = Column(DateTime(timezone=True))  # Última sincronización
    last_sync_at = Column(DateTime(timezone=True))  # Última sync exitosa
    
    # Información del servidor
    version = Column(String(50))  # Versión de raspServerNative
    ip_address = Column(String(45))  # IPv4 o IPv6
    
    # Estadísticas
    clients_count = Column(Integer, default=0)  # Número de clientes (cultivos) conectados
    clients_online = Column(Integer, default=0)  # Clientes online
    
    # Alertas
    alerts_enabled = Column(Boolean, default=True)
    alert_email = Column(String(255))  # Email específico para alertas de este servidor
    
    # Timestamps
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convierte a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'server_id': self.server_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'version': self.version,
            'ip_address': self.ip_address,
            'clients_count': self.clients_count,
            'clients_online': self.clients_online,
            'alerts_enabled': self.alerts_enabled,
            'alert_email': self.alert_email,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_online(self) -> bool:
        """Verifica si el servidor está online (sincronización en últimos 10 minutos)"""
        if not self.last_seen:
            return False
        from datetime import datetime, timedelta
        threshold = datetime.now() - timedelta(minutes=10)
        return self.last_seen >= threshold and self.status == 'online'
