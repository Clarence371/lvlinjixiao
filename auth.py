import jwt
import datetime
from functools import wraps
from flask import request, jsonify, g


SECRET_KEY = 'pbc-performance-jwt-secret-2026'
TOKEN_EXPIRE_HOURS = 24 * 7  # 7天


def create_token(user_id, username, role):
    """创建JWT令牌"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def verify_token(token):
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """验证令牌的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': '未提供认证令牌'}), 401
        
        token = auth_header[7:]
        payload = verify_token(token)
        if not payload:
            return jsonify({'success': False, 'message': '令牌无效或已过期'}), 401
        
        g.user_id = payload['user_id']
        g.username = payload['username']
        g.role = payload['role']
        
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.role != 'admin':
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated


def manager_required(f):
    """经理权限装饰器"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'message': '需要经理或管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated
