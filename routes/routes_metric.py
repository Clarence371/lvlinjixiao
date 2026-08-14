from flask import Blueprint, request, jsonify, g
from models import db, BusinessMetric, BusinessData, AchievementRule, AppraisalCycle, Employee
from auth import token_required, admin_required, manager_required
from datetime import datetime
import json

metric_bp = Blueprint('metric', __name__)


# ==================== 业务指标 ====================

@metric_bp.route('/metrics', methods=['GET'])
@token_required
def list_metrics():
    """获取业务指标列表"""
    metrics = BusinessMetric.query.filter_by(is_active=True).all()
    return jsonify({
        'success': True,
        'data': [m.to_dict() for m in metrics]
    })


@metric_bp.route('/metrics/<int:metric_id>', methods=['GET'])
@token_required
def get_metric(metric_id):
    """获取指标详情"""
    metric = BusinessMetric.query.get_or_404(metric_id)
    return jsonify({'success': True, 'data': metric.to_dict()})


@metric_bp.route('/metrics', methods=['POST'])
@admin_required
def create_metric():
    """创建业务指标"""
    data = request.get_json()
    
    if not data.get('name') or not data.get('code'):
        return jsonify({'success': False, 'message': '指标编码和名称不能为空'})
    
    if not data.get('weight'):
        return jsonify({'success': False, 'message': '权重不能为空'})
    
    if BusinessMetric.query.filter_by(code=data['code']).first():
        return jsonify({'success': False, 'message': '指标编码已存在'})
    
    metric = BusinessMetric(
        code=data['code'],
        name=data['name'],
        metric_type=data.get('metric_type', 'quantitative'),
        unit=data.get('unit'),
        weight=float(data['weight']),
        target_value=data.get('target_value'),
        description=data.get('description'),
        is_active=data.get('is_active', True)
    )
    db.session.add(metric)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '业务指标创建成功', 'data': metric.to_dict()})


@metric_bp.route('/metrics/<int:metric_id>', methods=['PUT'])
@admin_required
def update_metric(metric_id):
    """更新业务指标"""
    metric = BusinessMetric.query.get_or_404(metric_id)
    data = request.get_json()
    
    for field in ['name', 'metric_type', 'unit', 'weight', 'target_value',
                  'description', 'is_active']:
        if field in data:
            setattr(metric, field, data[field])
    
    db.session.commit()
    return jsonify({'success': True, 'message': '业务指标更新成功', 'data': metric.to_dict()})


@metric_bp.route('/metrics/<int:metric_id>', methods=['DELETE'])
@admin_required
def delete_metric(metric_id):
    """删除业务指标（软删除）"""
    metric = BusinessMetric.query.get_or_404(metric_id)
    metric.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': '业务指标已删除'})


# ==================== 业务数据录入 ====================

@metric_bp.route('/data', methods=['GET'])
@token_required
def list_business_data():
    """获取业务数据列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    cycle_id = request.args.get('cycle_id', type=int)
    employee_id = request.args.get('employee_id', type=int)
    metric_id = request.args.get('metric_id', type=int)
    period = request.args.get('period', '')
    
    query = BusinessData.query
    
    # 权限过滤：HR和经理可以看所有，录入员/员工只能看自己和下属
    if g.role == 'employee':
        emp = Employee.query.filter_by(user_id=g.user_id).first()
        if emp:
            subordinate_ids = [s.id for s in emp.subordinates]
            subordinate_ids.append(emp.id)
            query = query.filter(BusinessData.employee_id.in_(subordinate_ids))
    
    if cycle_id:
        query = query.filter_by(cycle_id=cycle_id)
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if metric_id:
        query = query.filter_by(metric_id=metric_id)
    if period:
        query = query.filter_by(period=period)
    
    pagination = query.order_by(BusinessData.entered_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    return jsonify({
        'success': True,
        'data': {
            'items': [d.to_dict() for d in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages
        }
    })


@metric_bp.route('/data/<int:data_id>', methods=['GET'])
@token_required
def get_business_data(data_id):
    """获取单条业务数据"""
    data = BusinessData.query.get_or_404(data_id)
    return jsonify({'success': True, 'data': data.to_dict()})


@metric_bp.route('/data', methods=['POST'])
@token_required
def create_business_data():
    """录入业务数据"""
    data = request.get_json()
    
    if not all([data.get('employee_id'), data.get('metric_id'),
                data.get('cycle_id'), data.get('actual_value') is not None]):
        return jsonify({'success': False, 'message': '员工、指标、考核周期、实际值不能为空'})
    
    metric = BusinessMetric.query.get(data['metric_id'])
    target_value = data.get('target_value') or metric.target_value if metric else None
    
    record = BusinessData(
        employee_id=data['employee_id'],
        metric_id=data['metric_id'],
        cycle_id=data['cycle_id'],
        period=data.get('period'),
        actual_value=float(data['actual_value']),
        target_value=target_value,
        entered_by=g.user_id
    )
    record.calculate_achievement()
    db.session.add(record)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '业务数据录入成功', 'data': record.to_dict()})


@metric_bp.route('/data/batch', methods=['POST'])
@token_required
def batch_create_business_data():
    """批量录入业务数据"""
    data = request.get_json()
    records = data.get('records', [])
    
    if not records:
        return jsonify({'success': False, 'message': '没有要录入的数据'})
    
    created = 0
    updated = 0
    
    for r in records:
        existing = BusinessData.query.filter_by(
            employee_id=r['employee_id'],
            metric_id=r['metric_id'],
            cycle_id=r['cycle_id'],
            period=r.get('period')
        ).first()
        
        if existing:
            existing.actual_value = float(r['actual_value'])
            existing.target_value = r.get('target_value')
            existing.entered_by = g.user_id
            existing.calculate_achievement()
            updated += 1
        else:
            metric = BusinessMetric.query.get(r['metric_id'])
            target_value = r.get('target_value') or (metric.target_value if metric else None)
            record = BusinessData(
                employee_id=r['employee_id'],
                metric_id=r['metric_id'],
                cycle_id=r['cycle_id'],
                period=r.get('period'),
                actual_value=float(r['actual_value']),
                target_value=target_value,
                entered_by=g.user_id
            )
            record.calculate_achievement()
            db.session.add(record)
            created += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'批量录入完成：新增{created}条，更新{updated}条'
    })


@metric_bp.route('/data/<int:data_id>', methods=['PUT'])
@token_required
def update_business_data(data_id):
    """更新业务数据"""
    record = BusinessData.query.get_or_404(data_id)
    data = request.get_json()
    
    for field in ['actual_value', 'target_value', 'period']:
        if field in data and data[field] is not None:
            setattr(record, field, data[field])
    
    record.calculate_achievement()
    record.entered_by = g.user_id
    db.session.commit()
    
    return jsonify({'success': True, 'message': '业务数据更新成功', 'data': record.to_dict()})


@metric_bp.route('/data/<int:data_id>', methods=['DELETE'])
@admin_required
def delete_business_data(data_id):
    """删除业务数据"""
    record = BusinessData.query.get_or_404(data_id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True, 'message': '业务数据已删除'})


# ==================== 达成规则 ====================

@metric_bp.route('/rules', methods=['GET'])
@token_required
def list_rules():
    """获取达成规则列表"""
    rules = AchievementRule.query.all()
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in rules]
    })


@metric_bp.route('/rules', methods=['POST'])
@admin_required
def create_rule():
    """创建达成规则"""
    data = request.get_json()
    
    rule = AchievementRule(
        metric_id=data.get('metric_id'),
        position_type=data.get('position_type', '通用'),
        rule_type=data.get('rule_type', 'ceiling'),
        max_rate=data.get('max_rate'),
        threshold=data.get('threshold'),
        description=data.get('description')
    )
    db.session.add(rule)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '达成规则创建成功', 'data': rule.to_dict()})


@metric_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@admin_required
def update_rule(rule_id):
    """更新达成规则"""
    rule = AchievementRule.query.get_or_404(rule_id)
    data = request.get_json()
    
    for field in ['metric_id', 'position_type', 'rule_type', 'max_rate', 'threshold', 'description']:
        if field in data:
            setattr(rule, field, data[field])
    
    db.session.commit()
    return jsonify({'success': True, 'message': '达成规则更新成功', 'data': rule.to_dict()})


@metric_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@admin_required
def delete_rule(rule_id):
    """删除达成规则"""
    rule = AchievementRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    return jsonify({'success': True, 'message': '达成规则已删除'})


# ==================== 统计汇总 ====================

@metric_bp.route('/statistics', methods=['GET'])
@token_required
def get_statistics():
    """获取统计汇总"""
    cycle_id = request.args.get('cycle_id', type=int)
    
    if not cycle_id:
        cycle = AppraisalCycle.query.filter_by(status='active').order_by(
            AppraisalCycle.start_date.desc()
        ).first()
        cycle_id = cycle.id if cycle else None
    
    if not cycle_id:
        return jsonify({'success': True, 'data': {}})
    
    cycle = AppraisalCycle.query.get(cycle_id)
    
    # 各部门完成情况
    from models import Department
    departments = Department.query.all()
    
    dept_stats = []
    for dept in departments:
        emps = [e.id for e in dept.employees.filter_by(status='active').all()]
        if not emps:
            continue
        
        from models import Appraisal
        total = Appraisal.query.filter_by(cycle_id=cycle_id).filter(
            Appraisal.employee_id.in_(emps)
        ).count()
        completed = Appraisal.query.filter_by(cycle_id=cycle_id, final_status='completed').filter(
            Appraisal.employee_id.in_(emps)
        ).count()
        
        dept_stats.append({
            'department': dept.name,
            'total': total,
            'completed': completed,
            'rate': round(completed/total*100, 1) if total > 0 else 0
        })
    
    return jsonify({
        'success': True,
        'data': {
            'cycle': cycle.to_dict() if cycle else None,
            'departments': dept_stats
        }
    })
