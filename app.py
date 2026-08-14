from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from models import db
import json


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    
    # 注册蓝图
    from routes.routes_auth import auth_bp
    from routes.routes_employee import employee_bp
    from routes.routes_appraisal import appraisal_bp
    from routes.routes_metric import metric_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(employee_bp, url_prefix='/api/employee')
    app.register_blueprint(appraisal_bp, url_prefix='/api/appraisal')
    app.register_blueprint(metric_bp, url_prefix='/api/metric')
    
    # 健康检查
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'PBC Performance System'})
    
    # 静态页面路由
    @app.route('/')
    def index():
        return send_static('login.html')
    
    @app.route('/login.html')
    def login_page():
        return send_static('login.html')
    
    @app.route('/dashboard.html')
    def dashboard_page():
        return send_static('dashboard.html')
    
    @app.route('/employees.html')
    def employees_page():
        return send_static('employees.html')
    
    @app.route('/metrics.html')
    def metrics_page():
        return send_static('metrics.html')
    
    @app.route('/data-entry.html')
    def data_entry_page():
        return send_static('data-entry.html')
    
    @app.route('/appraisal-cycle.html')
    def appraisal_cycle_page():
        return send_static('appraisal-cycle.html')
    
    @app.route('/appraisal-template.html')
    def appraisal_template_page():
        return send_static('appraisal-template.html')
    
    @app.route('/appraisal-list.html')
    def appraisal_list_page():
        return send_static('appraisal-list.html')
    
    @app.route('/appraisal-form.html')
    def appraisal_form_page():
        return send_static('appraisal-form.html')
    
    @app.route('/reports.html')
    def reports_page():
        return send_static('reports.html')
    
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory('static', filename)
    
    # 初始化数据库
    with app.app_context():
        db.create_all()
        init_demo_data()
    
    return app


def send_static(filename):
    return send_from_directory('static', filename)


def init_demo_data():
    """初始化演示数据"""
    from models import User, Department, Employee, BusinessMetric, AppraisalCycle, AppraisalTemplate, Appraisal
    from datetime import date
    
    if User.query.first() is not None:
        print("[PBC] Demo data already exists, skipping...")
        return
    
    print("[PBC] Initializing demo data...")
    
    # 部门
    tech = Department(name='技术部', description='负责技术研发和产品开发')
    sales = Department(name='销售部', description='负责产品销售和客户管理')
    hr = Department(name='人事部', description='负责人力资源管理')
    ops = Department(name='运营部', description='负责日常运营管理')
    db.session.add_all([tech, sales, hr, ops])
    db.session.commit()
    
    # 员工
    emp1 = Employee(employee_no='EMP001', name='张明', position='技术总监', 
                    department_id=tech.id, status='active', join_date=date(2020, 1, 15),
                    phone='13800001001', email='zhangming@greener.com')
    
    emp2 = Employee(employee_no='EMP002', name='王芳', position='销售经理',
                    department_id=sales.id, manager_id=None, status='active', join_date=date(2021, 3, 20),
                    phone='13800001002', email='wangfang@greener.com')
    
    emp3 = Employee(employee_no='EMP003', name='李华', position='HR专员',
                    department_id=hr.id, manager_id=None, status='active', join_date=date(2021, 6, 1),
                    phone='13800001003', email='lihua@greener.com')
    
    emp4 = Employee(employee_no='EMP004', name='赵强', position='高级工程师',
                    department_id=tech.id, manager_id=emp1.id, status='active', join_date=date(2022, 1, 10),
                    phone='13800001004', email='zhaoqiang@greener.com')
    
    emp5 = Employee(employee_no='EMP005', name='周莉', position='销售代表',
                    department_id=sales.id, manager_id=emp2.id, status='active', join_date=date(2023, 2, 15),
                    phone='13800001005', email='zhouli@greener.com')
    
    emp6 = Employee(employee_no='EMP006', name='吴涛', position='运维工程师',
                    department_id=ops.id, manager_id=emp1.id, status='active', join_date=date(2022, 8, 1),
                    phone='13800001006', email='wutao@greener.com')
    
    db.session.add_all([emp1, emp2, emp3, emp4, emp5, emp6])
    db.session.commit()
    
    # 补充王芳和李华的上级
    emp2.manager_id = emp1.id
    emp3.manager_id = emp1.id
    db.session.commit()
    
    # 用户
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    
    manager = User(username='manager', role='manager', employee_id=emp1.id)
    manager.set_password('manager123')
    db.session.add(manager)
    
    employee = User(username='employee', role='employee', employee_id=emp2.id)
    employee.set_password('employee123')
    db.session.add(employee)
    
    zhaoqiang = User(username='zhaoqiang', role='employee', employee_id=emp4.id)
    zhaoqiang.set_password('zhaoqiang123')
    db.session.add(zhaoqiang)
    
    db.session.commit()
    
    # 业务指标
    metrics = [
        BusinessMetric(code='MET001', name='销售额', metric_type='quantitative',
                      unit='万元', weight=30, target_value=100,
                      description='月度销售额目标达成情况'),
        BusinessMetric(code='MET002', name='客户满意度', metric_type='quantitative',
                      unit='分', weight=25, target_value=95,
                      description='客户评分满意度（百分制）'),
        BusinessMetric(code='MET003', name='产品上架率', metric_type='quantitative',
                      unit='%', weight=20, target_value=90,
                      description='新产品按时上架比例'),
        BusinessMetric(code='MET004', name='客户回购率', metric_type='quantitative',
                      unit='%', weight=15, target_value=40,
                      description='老客户回头购买比例'),
        BusinessMetric(code='MET005', name='团队协作', metric_type='qualitative',
                      weight=10,
                      description='团队合作、沟通与跨部门协作表现'),
    ]
    db.session.add_all(metrics)
    db.session.commit()
    
    # 考核模板
    template = AppraisalTemplate(
        name='标准绩效考核模板',
        description='适用于全体员工的绩效考核模板，包含5项核心指标',
        position_type='通用',
        metrics=json.dumps([
            {'metric_id': 1, 'weight': 30, 'order': 1},
            {'metric_id': 2, 'weight': 25, 'order': 2},
            {'metric_id': 3, 'weight': 20, 'order': 3},
            {'metric_id': 4, 'weight': 15, 'order': 4},
            {'metric_id': 5, 'weight': 10, 'order': 5},
        ]),
        is_active=True
    )
    db.session.add(template)
    db.session.commit()
    
    # 考核周期
    cycle = AppraisalCycle(
        name='2026年Q3绩效考核',
        year=2026,
        quarter=3,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 9, 30),
        self_review_start=date(2026, 9, 15),
        self_review_end=date(2026, 9, 25),
        manager_review_start=date(2026, 9, 26),
        manager_review_end=date(2026, 9, 30),
        status='active',
        remark='2026年第三季度全员绩效考核'
    )
    db.session.add(cycle)
    db.session.commit()
    
    # 生成考核单
    for emp in [emp1, emp2, emp3, emp4, emp5, emp6]:
        appraisal = Appraisal(
            cycle_id=cycle.id,
            employee_id=emp.id,
            template_id=template.id,
            manager_id=emp.manager_id,
            final_status='pending'
        )
        db.session.add(appraisal)
    
    db.session.commit()
    
    print("[PBC] Demo data initialized successfully!")
    print(f"[PBC] Departments: 4, Employees: 6, Metrics: 5")
    print("[PBC] Users: admin/admin123, manager/manager123, employee/employee123")


app = create_app()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("PBC Performance Management System")
    print("="*50)
    app.run(host='0.0.0.0', port=8000, debug=False)
