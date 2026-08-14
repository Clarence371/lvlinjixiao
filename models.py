from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class Department(db.Model):
    """部门"""
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    manager_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    children = db.relationship('Department', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'manager_id': self.manager_id,
            'description': self.description
        }


class Employee(db.Model):
    """员工"""
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    employee_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    name_pinyin = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    position = db.Column(db.String(100), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    join_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active')  # active/inactive/resigned
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    department = db.relationship('Department', backref='employees')
    manager = db.relationship('Employee', remote_side=[id], backref='subordinates')
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_no': self.employee_no,
            'name': self.name,
            'name_pinyin': self.name_pinyin,
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'department_id': self.department_id,
            'department': self.department.to_dict() if self.department else None,
            'position': self.position,
            'manager_id': self.manager_id,
            'manager': self.manager.name if self.manager else None,
            'join_date': self.join_date.isoformat() if self.join_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class User(db.Model):
    """系统用户"""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin/manager/employee
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    employee = db.relationship('Employee', backref='user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'employee_id': self.employee_id,
            'is_active': self.is_active
        }


class BusinessMetric(db.Model):
    """业务指标"""
    __tablename__ = 'business_metric'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    metric_type = db.Column(db.String(20), nullable=False)  # quantitative/qualitative
    unit = db.Column(db.String(20), nullable=True)  # %, 元, 次, etc
    weight = db.Column(db.Float, nullable=False)  # 权重百分比
    target_value = db.Column(db.Float, nullable=True)
    description = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'metric_type': self.metric_type,
            'unit': self.unit,
            'weight': self.weight,
            'target_value': self.target_value,
            'description': self.description,
            'is_active': self.is_active
        }


class AppraisalTemplate(db.Model):
    """考核模板"""
    __tablename__ = 'appraisal_template'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    position_type = db.Column(db.String(50), nullable=True)  # 通用/管理层/销售/技术
    metrics = db.Column(db.Text, nullable=True)  # JSON: [{metric_id, weight, order}]
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def get_metrics(self):
        if self.metrics:
            return json.loads(self.metrics)
        return []
    
    def set_metrics(self, metrics_list):
        self.metrics = json.dumps(metrics_list, ensure_ascii=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'position_type': self.position_type,
            'metrics': self.get_metrics(),
            'is_active': self.is_active
        }


class AppraisalCycle(db.Model):
    """考核周期"""
    __tablename__ = 'appraisal_cycle'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer, nullable=True)  # 1-4 or None for annual
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    self_review_start = db.Column(db.Date, nullable=True)
    self_review_end = db.Column(db.Date, nullable=True)
    manager_review_start = db.Column(db.Date, nullable=True)
    manager_review_end = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft/active/completed
    remark = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'year': self.year,
            'quarter': self.quarter,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'self_review_start': self.self_review_start.isoformat() if self.self_review_start else None,
            'self_review_end': self.self_review_end.isoformat() if self.self_review_end else None,
            'manager_review_start': self.manager_review_start.isoformat() if self.manager_review_start else None,
            'manager_review_end': self.manager_review_end.isoformat() if self.manager_review_end else None,
            'status': self.status,
            'remark': self.remark
        }


class Appraisal(db.Model):
    """考核单"""
    __tablename__ = 'appraisal'
    id = db.Column(db.Integer, primary_key=True)
    cycle_id = db.Column(db.Integer, db.ForeignKey('appraisal_cycle.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('appraisal_template.id'), nullable=True)
    
    # Self assessment
    self_assessment_status = db.Column(db.String(20), default='pending')  # pending/submitted
    self_assessment = db.Column(db.Text, nullable=True)  # JSON: metrics data
    self_submitted_at = db.Column(db.DateTime, nullable=True)
    
    # Manager review
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    manager_assessment = db.Column(db.Text, nullable=True)  # JSON: manager scores
    manager_score = db.Column(db.Float, nullable=True)  # 最终得分
    manager_submitted_at = db.Column(db.DateTime, nullable=True)
    
    # Final
    final_score = db.Column(db.Float, nullable=True)
    final_status = db.Column(db.String(20), default='pending')  # pending/self_review/manager_review/completed
    completed_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    cycle = db.relationship('AppraisalCycle', backref='appraisals')
    employee = db.relationship('Employee', foreign_keys=[employee_id])
    template = db.relationship('AppraisalTemplate')
    manager = db.relationship('Employee', foreign_keys=[manager_id])
    
    def calculate_final_score(self):
        """计算最终得分"""
        if not self.manager_assessment:
            return None
        try:
            data = json.loads(self.manager_assessment)
            total = sum(item.get('score', 0) * item.get('weight', 0) / 100 
                      for item in data if item.get('weight'))
            return round(total, 2)
        except:
            return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'cycle_id': self.cycle_id,
            'cycle': self.cycle.to_dict() if self.cycle else None,
            'employee_id': self.employee_id,
            'employee': self.employee.to_dict() if self.employee else None,
            'template_id': self.template_id,
            'self_assessment_status': self.self_assessment_status,
            'self_assessment': json.loads(self.self_assessment) if self.self_assessment else None,
            'self_submitted_at': self.self_submitted_at.isoformat() if self.self_submitted_at else None,
            'manager_id': self.manager_id,
            'manager': self.manager.to_dict() if self.manager else None,
            'manager_assessment': json.loads(self.manager_assessment) if self.manager_assessment else None,
            'manager_score': self.manager_score,
            'manager_submitted_at': self.manager_submitted_at.isoformat() if self.manager_submitted_at else None,
            'final_score': self.final_score,
            'final_status': self.final_status,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class BusinessData(db.Model):
    """业务数据录入"""
    __tablename__ = 'business_data'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    metric_id = db.Column(db.Integer, db.ForeignKey('business_metric.id'), nullable=False)
    cycle_id = db.Column(db.Integer, db.ForeignKey('appraisal_cycle.id'), nullable=False)
    period = db.Column(db.String(50), nullable=True)  # 月份如 "2026-08"
    actual_value = db.Column(db.Float, nullable=False)
    target_value = db.Column(db.Float, nullable=True)
    achievement_rate = db.Column(db.Float, nullable=True)  # 达成率 %
    entered_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    entered_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    employee = db.relationship('Employee', backref='business_data')
    metric = db.relationship('BusinessMetric', backref='business_data')
    cycle = db.relationship('AppraisalCycle', backref='business_data')
    enterer = db.relationship('User')
    
    def calculate_achievement(self):
        if self.target_value and self.target_value > 0:
            self.achievement_rate = round((self.actual_value / self.target_value) * 100, 2)
        else:
            self.achievement_rate = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee': self.employee.to_dict() if self.employee else None,
            'metric_id': self.metric_id,
            'metric': self.metric.to_dict() if self.metric else None,
            'cycle_id': self.cycle_id,
            'cycle': self.cycle.to_dict() if self.cycle else None,
            'period': self.period,
            'actual_value': self.actual_value,
            'target_value': self.target_value,
            'achievement_rate': self.achievement_rate,
            'entered_at': self.entered_at.isoformat() if self.entered_at else None
        }


class AchievementRule(db.Model):
    """达成规则"""
    __tablename__ = 'achievement_rule'
    id = db.Column(db.Integer, primary_key=True)
    metric_id = db.Column(db.Integer, db.ForeignKey('business_metric.id'), nullable=True)
    position_type = db.Column(db.String(50), nullable=True)  # 通用/管理层/销售
    rule_type = db.Column(db.String(20), nullable=False)  # ceiling/cap/floor
    max_rate = db.Column(db.Float, nullable=True)  # 上限（如 120%）
    threshold = db.Column(db.Float, nullable=True)  # 归零阈值
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    metric = db.relationship('BusinessMetric', backref='rules')
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_id': self.metric_id,
            'metric': self.metric.to_dict() if self.metric else None,
            'position_type': self.position_type,
            'rule_type': self.rule_type,
            'max_rate': self.max_rate,
            'threshold': self.threshold,
            'description': self.description
        }
