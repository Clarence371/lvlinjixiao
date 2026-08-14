from flask import Blueprint, request, jsonify, g
from models import db, User, Employee
from auth import create_token, token_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '请求数据无效'})
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})
    
    user = User.query.filter_by(username=username, is_active=True).first()
    
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': '用户名或密码错误'})
    
    employee_info = None
    if user.employee_id:
        emp = Employee.query.get(user.employee_id)
        if emp:
            employee_info = emp.to_dict()
    
    token = create_token(user.id, user.username, user.role)
    
    return jsonify({
        'success': True,
        'message': '登录成功',
        'data': {
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'employee': employee_info
            }
        }
    })


@auth_bp.route('/current-user', methods=['GET'])
@token_required
def get_current_user():
    """获取当前登录用户"""
    user = User.query.get(g.user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})
    
    employee_info = None
    if user.employee_id:
        emp = Employee.query.get(user.employee_id)
        if emp:
            employee_info = emp.to_dict()
    
    return jsonify({
        'success': True,
        'data': {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'employee': employee_info
        }
    })


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """修改密码"""
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not old_password or not new_password:
        return jsonify({'success': False, 'message': '密码不能为空'})
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': '新密码至少6位'})
    
    user = User.query.get(g.user_id)
    if not user.check_password(old_password):
        return jsonify({'success': False, 'message': '原密码错误'})
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '密码修改成功'})


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """退出登录"""
    return jsonify({'success': True, 'message': '已退出登录'})
