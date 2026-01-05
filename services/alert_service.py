# -*- coding: utf-8 -*-
"""
Servicio de Alertas para FungiCloud
Monitorea servidores offline y envía notificaciones
"""
import logging
import smtplib
import os
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import get_db_session
from models.local_server import LocalServer
from models.user import User
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = int(os.getenv('ALERT_CHECK_INTERVAL', 300))  # 5 min
    
    def start(self):
        """Inicia el monitor de alertas"""
        if self.running:
            logger.warning("Monitor de alertas ya está ejecutándose")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Monitor de alertas iniciado")
    
    def stop(self):
        """Detiene el monitor de alertas"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("Monitor de alertas detenido")
    
    def _monitor_loop(self):
        """Loop principal del monitor"""
        while self.running:
            try:
                self._check_offline_servers()
            except Exception as e:
                logger.error(f"Error en monitor de alertas: {e}")
            
            time.sleep(self.check_interval)
    
    def _check_offline_servers(self):
        """Verifica servidores offline y envía alertas"""
        threshold = datetime.now() - timedelta(minutes=15)
        
        with get_db_session() as session:
            offline_servers = session.query(LocalServer).filter(
                LocalServer.last_seen < threshold,
                LocalServer.status != 'offline',
                LocalServer.alerts_enabled == True
            ).all()
            
            for server in offline_servers:
                # Actualizar estado
                server.status = 'offline'
                
                # Obtener usuario
                user = session.query(User).filter_by(id=server.user_id).first()
                
                if user and user.is_active:
                    # Enviar alerta
                    self._send_alert_email(
                        user.email,
                        server.name,
                        server.last_seen
                    )
                    logger.warning(f"Alerta enviada: servidor {server.server_id} offline")
            
            session.commit()
    
    def _send_alert_email(self, to_email: str, server_name: str, last_seen: datetime):
        """Envía email de alerta"""
        try:
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            from_email = os.getenv('ALERT_EMAIL_FROM', 'alerts@fungicontrol.com')
            
            if not smtp_user or not smtp_password:
                logger.warning("SMTP no configurado, no se pueden enviar emails")
                return
            
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = f'⚠️ Servidor Offline: {server_name}'
            
            body = f"""
            <html>
            <body>
                <h2>⚠️ Alerta de Servidor Offline</h2>
                <p>Tu servidor <strong>{server_name}</strong> no se ha conectado en más de 15 minutos.</p>
                <p><strong>Última conexión:</strong> {last_seen.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Por favor verifica:</p>
                <ul>
                    <li>Conectividad a internet del servidor</li>
                    <li>Estado del servicio raspServerNative</li>
                    <li>Logs del sistema</li>
                </ul>
                <p>Si el problema persiste, contacta con soporte.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alerta enviada a {to_email}")
            
        except Exception as e:
            logger.error(f"Error enviando alerta: {e}")

# Instancia global
_alert_service = None

def get_alert_service() -> AlertService:
    """Obtiene la instancia del servicio de alertas"""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service

def start_alert_monitor():
    """Inicia el monitor de alertas"""
    service = get_alert_service()
    service.start()
