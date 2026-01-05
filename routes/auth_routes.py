# -*- coding: utf-8 -*-
"""
Rutas de autenticación para FungiCloud
"""
from flask import Blueprint, request, jsonify
import jwt
import os
import logging
from datetime import datetime, timedelta
from database import get_db_session
from models.user import User
from models.billing import UserBilling

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))

def create_token(user_id: int, email: str, is_admin: bool = False) -> str:
    """Crea un JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token: str) -> dict:
    """Verifica y decodifica un JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """Registra un nuevo usuario"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"success": False, "error": "Email y contraseña requeridos"}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        if len(password) < 8:
            return jsonify({"success": False, "error": "La contraseña debe tener al menos 8 caracteres"}), 400
        
        with get_db_session() as session:
            # Verificar si el usuario ya existe
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                return jsonify({"success": False, "error": "El email ya está registrado"}), 400
            
            # Crear usuario
            user = User(email=email)
            user.set_password(password)
            session.add(user)
            session.flush()
            
            # Crear billing con plan free
            billing = UserBilling(
                user_id=user.id,
                plan_type='free',
                plan_status='active'
            )
            session.add(billing)
            session.commit()
            
            # Crear token
            token = create_token(user.id, user.email, user.is_admin)
            
            logger.info(f"Usuario registrado: {email}")
            
            return jsonify({
                "success": True,
                "message": "Usuario creado exitosamente",
                "token": token,
                "user": user.to_dict()
            }), 201
            
    except Exception as e:
        logger.error(f"Error en registro: {e}")
        return jsonify({"success": False, "error": "Error al registrar usuario"}), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Inicia sesión de usuario"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"success": False, "error": "Email y contraseña requeridos"}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        with get_db_session() as session:
            user = session.query(User).filter_by(email=email).first()
            
            if not user or not user.check_password(password):
                return jsonify({"success": False, "error": "Credenciales inválidas"}), 401
            
            if not user.is_active:
                return jsonify({"success": False, "error": "Usuario desactivado"}), 403
            
            # Crear token
            token = create_token(user.id, user.email, user.is_admin)
            
            logger.info(f"Login exitoso: {email}")
            
            return jsonify({
                "success": True,
                "token": token,
                "user": user.to_dict()
            })
            
    except Exception as e:
        logger.error(f"Error en login: {e}")
        return jsonify({"success": False, "error": "Error al iniciar sesión"}), 500

@auth_bp.route('/auth/verify', methods=['GET'])
def verify():
    """Verifica un token JWT"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "error": "Token requerido"}), 401
        
        token = auth_header.replace('Bearer ', '')
        payload = verify_token(token)
        
        if not payload:
            return jsonify({"success": False, "error": "Token inválido o expirado"}), 401
        
        with get_db_session() as session:
            user = session.query(User).filter_by(id=payload['user_id']).first()
            
            if not user or not user.is_active:
                return jsonify({"success": False, "error": "Usuario no encontrado o inactivo"}), 404
            
            return jsonify({
                "success": True,
                "user": user.to_dict()
            })
            
    except Exception as e:
        logger.error(f"Error en verificación: {e}")
        return jsonify({"success": False, "error": "Error al verificar token"}), 500
