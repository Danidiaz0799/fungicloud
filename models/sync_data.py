# -*- coding: utf-8 -*-
"""
Modelo de Datos de Sincronización
Almacena datos agregados que los servidores locales envían al cloud
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float, Text
from sqlalchemy.sql import func
from database import Base

class SyncData(Base):
    __tablename__ = 'sync_data'
    
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('local_servers.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Timestamp de los datos
    data_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Datos de sensores (agregados de últimos 15 min)
    avg_temperature = Column(Float)
    min_temperature = Column(Float)
    max_temperature = Column(Float)
    avg_humidity = Column(Float)
    min_humidity = Column(Float)
    max_humidity = Column(Float)
    avg_light_intensity = Column(Float)
    avg_pressure = Column(Float)
    
    # Contadores de clientes
    clients_total = Column(Integer, default=0)
    clients_online = Column(Integer, default=0)
    
    # Métricas
    readings_count = Column(Integer, default=0)  # Lecturas de sensores en ventana
    
    # Timestamp de recepción
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        """Convierte a diccionario"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'user_id': self.user_id,
            'data_timestamp': self.data_timestamp.isoformat() if self.data_timestamp else None,
            'avg_temperature': self.avg_temperature,
            'min_temperature': self.min_temperature,
            'max_temperature': self.max_temperature,
            'avg_humidity': self.avg_humidity,
            'min_humidity': self.min_humidity,
            'max_humidity': self.max_humidity,
            'avg_light_intensity': self.avg_light_intensity,
            'avg_pressure': self.avg_pressure,
            'clients_total': self.clients_total,
            'clients_online': self.clients_online,
            'readings_count': self.readings_count,
            'received_at': self.received_at.isoformat() if self.received_at else None
        }

class SyncEvent(Base):
    __tablename__ = 'sync_events'
    
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('local_servers.id'), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)  # sync_success, sync_failed, server_online, server_offline
    message = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def to_dict(self):
        """Convierte a diccionario"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'event_type': self.event_type,
            'message': self.message,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
