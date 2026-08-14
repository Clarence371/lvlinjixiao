from flask import Blueprint, request, jsonify, g
from models import db, Department, Employee, User
from auth import token_required, admin_required, manager_required

employee_bp = Blueprint('employee', __name__)


@employee_bp.route('/departments', methods=['GET'])
@token_required
def list_departments():
    """获取部门列表"""
    departments = Department.query.all()
    return jsonify({
        'success': True,
        'data': [d.to_dict() for d in departments]
    })


@employee_bp.route('/departments', methods=['POST'])
@admin_required
def create_department():
    """创建部门"""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': '部门名称不能为空'})
    
    if Department.query.filter_by(name=data['name']).first():
        return jsonify({'success': False, 'message': '部门已存在'})
    
    dept = Department(
        name=data['name'],
        description=data.get('description'),
        parent_id=data.get('parent_id')
    )
    db.session.add(dept)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '部门创建成功', 'data': dept.to_dict()})


@employee_bp.route('/departments/<int:dept_id>', methods=['PUT'])
@admin_required
def update_department(dept_id):
    """更新部门"""
    dept = Department.query.get_or_404(dept_id)
    data = request.get_json()
    
    if data.get('name'):
        dept.name = data['name']
    if 'description' in data:
        dept.description = data['description']
    if 'parent_id' in data:
        dept.parent_id = data['parent_id']
    
    db.session.commit()
    return jsonify({'success': True, 'message': '部门更新成功', 'data': dept.to_dict()})


@employee_bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@admin_required
def delete_department(dept_id):
    """删除部门"""
    dept = Department.query.get_or_404(dept_id)
    if dept.employees.count() > 0:
        return jsonify({'success': False, 'message': '该部门下有员工，无法删除'})
    db.session.delete(dept)
    db.session.commit()
    return jsonify({'success': True, 'message': '部门删除成功'})


@employee_bp.route('/list', methods=['GET'])
@token_required
def list_employees():
    """获取员工列表（带权限过滤）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    department_id = request.args.get('department_id', type=int)
    status = request.args.get('status', 'active')
    keyword = request.args.get('keyword', '')
    
    query = Employee.query
    
    # 普通员工只能看自己和下属
    if g.role == 'employee':
        query = query.filter(Employee.id == g.user.employee_id if hasattr(g, 'user') else False)
    # 经理可以看下下属
    elif g.role == 'manager':
        emp = Employee.query.filter_by(user_id=g.user_id).first()
        if emp:
            subordinate_ids = [s.id for s in emp.subordinates]
            subordinate_ids.append(emp.id)
            query = query.filter(Employee.id.in_(subordinate_ids))
    
    if department_id:
        query = query.filter_by(department_id=department_id)
    if status:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(
            db.or_(
                Employee.name.contains(keyword),
                Employee.employee_no.contains(keyword),
                Employee.position.contains(keyword)
            )
        )
    
    pagination = query.order_by(Employee.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    return jsonify({
        'success': True,
        'data': {
            'items': [e.to_dict() for e in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages
        }
    })


@employee_bp.route('/<int:emp_id>', methods=['GET'])
@token_required
def get_employee(emp_id):
    """获取员工详情"""
    emp = Employee.query.get_or_404(emp_id)
    
    # 权限检查
    if g.role == 'employee':
        current_emp = Employee.query.filter_by(user_id=g.user_id).first()
        if not current_emp or (emp.id != current_emp.id and emp.manager_id != current_emp.id):
            return jsonify({'success': False, 'message': '无权查看'})
    
    return jsonify({'success': True, 'data': emp.to_dict()})


@employee_bp.route('', methods=['POST'])
@admin_required
def create_employee():
    """创建员工"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'success': False, 'message': '姓名不能为空'})
    if not data.get('employee_no'):
        return jsonify({'success': False, 'message': '工号不能为空'})
    
    if Employee.query.filter_by(employee_no=data['employee_no']).first():
        return jsonify({'success': False, 'message': '工号已存在'})
    
    emp = Employee(
        employee_no=data['employee_no'],
        name=data['name'],
        name_pinyin=data.get('name_pinyin'),
        gender=data.get('gender'),
        phone=data.get('phone'),
        email=data.get('email'),
        department_id=data.get('department_id'),
        position=data.get('position'),
        manager_id=data.get('manager_id'),
        join_date=data.get('join_date'),
        status=data.get('status', 'active')
    )
    db.session.add(emp)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '员工创建成功', 'data': emp.to_dict()})


@employee_bp.route('/<int:emp_id>', methods=['PUT'])
@admin_required
def update_employee(emp_id):
    """更新员工"""
    emp = Employee.query.get_or_404(emp_id)
    data = request.get_json()
    
    for field in ['name', 'name_pinyin', 'gender', 'phone', 'email',
                  'department_id', 'position', 'manager_id', 'status']:
        if field in data:
            setattr(emp, field, data[field])
    
    db.session.commit()
    return jsonify({'success': True, 'message': '员工更新成功', 'data': emp.to_dict()})


@employee_bp.route('/<int:emp_id>', methods=['DELETE'])
@admin_required
def delete_employee(emp_id):
    """删除员工（软删除改为离职状态）"""
    emp = Employee.query.get_or_404(emp_id)
    emp.status = 'resigned'
    db.session.commit()
    return jsonify({'success': True, 'message': '员工已设为离职状态'})


@employee_bp.route('/<int:emp_id>/subordinates', methods=['GET'])
@token_required
def list_subordinates(emp_id):
    """获取下属列表"""
    emp = Employee.query.get_or_404(emp_id)
    subs = emp.subordinates.filter_by(status='active').all()
    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in subs]
    })
