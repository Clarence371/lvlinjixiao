from flask import Blueprint, request, jsonify, g
from models import db, AppraisalCycle, AppraisalTemplate, Appraisal, Employee, User, BusinessMetric, BusinessData
from auth import token_required, admin_required, manager_required
from datetime import datetime, date
import json

def parse_date(val):
    """Convert 'YYYY-MM-DD' string to Python date, or return None."""
    if not val:
        return None
    if isinstance(val, (date, datetime)):
        return val if isinstance(val, date) else val.date()
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y-%m-%dT%H:%M:%S'):
        try:
            dt = datetime.strptime(str(val)[:10], fmt)
            return dt.date()
        except ValueError:
            continue
    return None

appraisal_bp = Blueprint('appraisal', __name__)


# ==================== 考核周期 ====================

@appraisal_bp.route('/cycles', methods=['GET'])
@token_required
def list_cycles():
    """获取考核周期列表"""
    cycles = AppraisalCycle.query.order_by(AppraisalCycle.start_date.desc()).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in cycles]
    })


@appraisal_bp.route('/cycles/<int:cycle_id>', methods=['GET'])
@token_required
def get_cycle(cycle_id):
    """获取考核周期详情"""
    cycle = AppraisalCycle.query.get_or_404(cycle_id)
    return jsonify({'success': True, 'data': cycle.to_dict()})


@appraisal_bp.route('/cycles', methods=['POST'])
@admin_required
def create_cycle():
    """创建考核周期"""
    data = request.get_json()
    
    required = ['name', 'year', 'start_date', 'end_date']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field}不能为空'})
    
    cycle = AppraisalCycle(
        name=data['name'],
        year=int(data['year']),
        quarter=data.get('quarter'),
        start_date=parse_date(data['start_date']),
        end_date=parse_date(data['end_date']),
        self_review_start=parse_date(data.get('self_review_start')),
        self_review_end=parse_date(data.get('self_review_end')),
        manager_review_start=parse_date(data.get('manager_review_start')),
        manager_review_end=parse_date(data.get('manager_review_end')),
        status=data.get('status', 'draft'),
        remark=data.get('remark')
    )
    db.session.add(cycle)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '考核周期创建成功', 'data': cycle.to_dict()})


@appraisal_bp.route('/cycles/<int:cycle_id>', methods=['PUT'])
@admin_required
def update_cycle(cycle_id):
    """更新考核周期"""
    cycle = AppraisalCycle.query.get_or_404(cycle_id)
    data = request.get_json()
    
    date_fields = ['start_date', 'end_date', 'self_review_start', 'self_review_end',
                     'manager_review_start', 'manager_review_end']
    for field in ['name', 'year', 'quarter', 'status', 'remark']:
        if field in data:
            setattr(cycle, field, data[field])
    for field in date_fields:
        if field in data:
            setattr(cycle, field, parse_date(data[field]))
    
    db.session.commit()
    return jsonify({'success': True, 'message': '考核周期更新成功', 'data': cycle.to_dict()})


@appraisal_bp.route('/cycles/<int:cycle_id>', methods=['DELETE'])
@admin_required
def delete_cycle(cycle_id):
    """删除考核周期"""
    cycle = AppraisalCycle.query.get_or_404(cycle_id)
    if cycle.appraisals:
        return jsonify({'success': False, 'message': '该周期下已有考核记录，无法删除'})
    db.session.delete(cycle)
    db.session.commit()
    return jsonify({'success': True, 'message': '考核周期删除成功'})


# ==================== 考核模板 ====================

@appraisal_bp.route('/templates', methods=['GET'])
@token_required
def list_templates():
    """获取考核模板列表"""
    templates = AppraisalTemplate.query.all()
    return jsonify({
        'success': True,
        'data': [t.to_dict() for t in templates]
    })


@appraisal_bp.route('/templates/<int:template_id>', methods=['GET'])
@token_required
def get_template(template_id):
    """获取模板详情（含指标明细）"""
    template = AppraisalTemplate.query.get_or_404(template_id)
    result = template.to_dict()
    
    # 补充指标详情
    metrics_data = []
    for m in template.get_metrics():
        metric = BusinessMetric.query.get(m.get('metric_id'))
        if metric:
            metrics_data.append({
                'metric': metric.to_dict(),
                'weight': m.get('weight', 0),
                'order': m.get('order', 0)
            })
    result['metrics_detail'] = metrics_data
    return jsonify({'success': True, 'data': result})


@appraisal_bp.route('/templates', methods=['POST'])
@admin_required
def create_template():
    """创建考核模板"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'success': False, 'message': '模板名称不能为空'})
    
    template = AppraisalTemplate(
        name=data['name'],
        description=data.get('description'),
        position_type=data.get('position_type', '通用'),
        metrics=json.dumps(data.get('metrics', []), ensure_ascii=False),
        is_active=data.get('is_active', True)
    )
    db.session.add(template)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '模板创建成功', 'data': template.to_dict()})


@appraisal_bp.route('/templates/<int:template_id>', methods=['PUT'])
@admin_required
def update_template(template_id):
    """更新考核模板"""
    template = AppraisalTemplate.query.get_or_404(template_id)
    data = request.get_json()
    
    for field in ['name', 'description', 'position_type', 'is_active']:
        if field in data:
            setattr(template, field, data[field])
    if 'metrics' in data:
        template.set_metrics(data['metrics'])
    
    db.session.commit()
    return jsonify({'success': True, 'message': '模板更新成功', 'data': template.to_dict()})


@appraisal_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@admin_required
def delete_template(template_id):
    """删除考核模板"""
    template = AppraisalTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    return jsonify({'success': True, 'message': '模板删除成功'})


# ==================== 考核单 ====================

@appraisal_bp.route('/list', methods=['GET'])
@token_required
def list_appraisals():
    """获取考核单列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    cycle_id = request.args.get('cycle_id', type=int)
    status = request.args.get('status', '')
    
    query = Appraisal.query
    
    # 权限过滤
    if g.role == 'employee':
        emp = Employee.query.filter_by(user_id=g.user_id).first()
        if emp:
            query = query.filter_by(employee_id=emp.id)
    elif g.role == 'manager':
        emp = Employee.query.filter_by(user_id=g.user_id).first()
        if emp:
            subordinate_ids = [s.id for s in emp.subordinates]
            query = query.filter(
                db.or_(
                    Appraisal.employee_id.in_(subordinate_ids),
                    Appraisal.manager_id == emp.id
                )
            )
    
    if cycle_id:
        query = query.filter_by(cycle_id=cycle_id)
    if status:
        query = query.filter_by(final_status=status)
    
    pagination = query.order_by(Appraisal.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    return jsonify({
        'success': True,
        'data': {
            'items': [a.to_dict() for a in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages
        }
    })


@appraisal_bp.route('/<int:appraisal_id>', methods=['GET'])
@token_required
def get_appraisal(appraisal_id):
    """获取考核单详情"""
    appraisal = Appraisal.query.get_or_404(appraisal_id)
    
    # 权限检查
    if g.role == 'employee':
        emp = Employee.query.filter_by(user_id=g.user_id).first()
        if not emp or appraisal.employee_id != emp.id:
            return jsonify({'success': False, 'message': '无权查看'})
    
    return jsonify({'success': True, 'data': appraisal.to_dict()})


@appraisal_bp.route('/batch-create', methods=['POST'])
@admin_required
def batch_create_appraisals():
    """批量创建考核单"""
    data = request.get_json()
    cycle_id = data.get('cycle_id')
    employee_ids = data.get('employee_ids', [])
    
    if not cycle_id:
        return jsonify({'success': False, 'message': 'cycle_id不能为空'})
    
    cycle = AppraisalCycle.query.get_or_404(cycle_id)
    template = AppraisalTemplate.query.filter_by(is_active=True).first()
    
    created = 0
    for emp_id in employee_ids:
        emp = Employee.query.get(emp_id)
        if not emp:
            continue
        if Appraisal.query.filter_by(cycle_id=cycle_id, employee_id=emp_id).first():
            continue
        
        # 找到上级
        manager_id = emp.manager_id
        
        appraisal = Appraisal(
            cycle_id=cycle_id,
            employee_id=emp_id,
            template_id=template.id if template else None,
            manager_id=manager_id,
            final_status='pending'
        )
        db.session.add(appraisal)
        created += 1
    
    db.session.commit()
    return jsonify({'success': True, 'message': f'成功创建{created}个考核单'})


@appraisal_bp.route('/<int:appraisal_id>/self-assessment', methods=['POST'])
@token_required
def submit_self_assessment(appraisal_id):
    """提交自评"""
    appraisal = Appraisal.query.get_or_404(appraisal_id)
    
    # 权限检查
    emp = Employee.query.filter_by(user_id=g.user_id).first()
    if not emp or appraisal.employee_id != emp.id:
        return jsonify({'success': False, 'message': '无权操作'})
    
    data = request.get_json()
    
    appraisal.self_assessment = json.dumps(data.get('metrics', []), ensure_ascii=False)
    appraisal.self_assessment_status = 'submitted'
    appraisal.self_submitted_at = datetime.now()
    appraisal.updated_at = datetime.now()
    
    if appraisal.final_status == 'pending':
        appraisal.final_status = 'self_review'
    
    db.session.commit()
    return jsonify({'success': True, 'message': '自评提交成功'})


@appraisal_bp.route('/<int:appraisal_id>/manager-review', methods=['POST'])
@manager_required
def submit_manager_review(appraisal_id):
    """提交上级评分"""
    appraisal = Appraisal.query.get_or_404(appraisal_id)
    data = request.get_json()
    
    # 经理只能评自己下属
    emp = Employee.query.filter_by(user_id=g.user_id).first()
    if not emp or appraisal.employee_id not in [s.id for s in emp.subordinates]:
        return jsonify({'success': False, 'message': '只能评分自己下属的考核'})
    
    appraisal.manager_assessment = json.dumps(data.get('metrics', []), ensure_ascii=False)
    appraisal.manager_score = appraisal.calculate_final_score()
    appraisal.manager_submitted_at = datetime.now()
    appraisal.final_status = 'completed'
    appraisal.final_score = appraisal.manager_score
    appraisal.completed_at = datetime.now()
    appraisal.updated_at = datetime.now()
    
    db.session.commit()
    return jsonify({'success': True, 'message': '评分提交成功', 'final_score': appraisal.final_score})


@appraisal_bp.route('/my', methods=['GET'])
@token_required
def my_appraisals():
    """获取我的考核记录"""
    emp = Employee.query.filter_by(user_id=g.user_id).first()
    if not emp:
        return jsonify({'success': False, 'message': '未找到关联员工'})
    
    appraisals = Appraisal.query.filter_by(employee_id=emp.id).order_by(
        Appraisal.created_at.desc()
    ).all()
    
    return jsonify({
        'success': True,
        'data': [a.to_dict() for a in appraisals]
    })


@appraisal_bp.route('/team', methods=['GET'])
@manager_required
def team_appraisals():
    """获取团队考核记录"""
    emp = Employee.query.filter_by(user_id=g.user_id).first()
    if not emp:
        return jsonify({'success': False, 'message': '未找到关联员工'})
    
    subordinate_ids = [s.id for s in emp.subordinates]
    appraisals = Appraisal.query.filter(
        Appraisal.employee_id.in_(subordinate_ids)
    ).order_by(Appraisal.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [a.to_dict() for a in appraisals]
    })
