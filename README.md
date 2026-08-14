# 绿林工具绩效管理系统

基于 Python Flask + SQLite 的独立绩效管理系统，前端采用微软 Fluent Design 风格。

> ⚠️ 本系统为**独立开发**，不依赖 Frappe Framework。

---

## 系统信息

- **访问地址**: http://118.190.216.34:8000
- **Python 版本**: 3.10+
- **数据库**: SQLite（内置，无需安装）
- **端口**: 8000

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python Flask + SQLAlchemy + JWT |
| 前端 | 原生 HTML5 + CSS3 + JavaScript |
| 数据库 | SQLite 3 |
| 认证 | JWT (PyJWT) |
| 部署 | 原生 Python 进程（无 Docker） |

---

## 快速安装

```bash
# 1. 克隆代码
git clone <repo-url>
cd pbc_system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动（自动创建数据库和演示数据）
python app.py

# 4. 访问
# http://localhost:8000
```

---

## 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 系统管理员 | admin | admin123 |
| 部门经理 | manager | manager123 |
| 普通员工 | employee | employee123 |
| 普通员工 | zhaoqiang | zhaoqiang123 |

> ⚠️ 正式环境请务必修改默认密码

---

## 功能模块

- **工作台** - 统计概览、快捷入口、待办提醒
- **员工管理** - 员工增删改查、部门管理
- **业务指标** - 指标定义与权重配置
- **数据录入** - 业务数据批量录入
- **考核周期** - 考核周期创建与时间设置
- **考核模板** - 考核指标模板配置
- **考核管理** - 考核单列表、自评/上级评分
- **报表中心** - 部门完成率、得分排行榜

---

## 目录结构

```
pbc_system/
├── app.py                  # Flask 应用入口 + 演示数据初始化
├── config.py               # 配置文件（JWT密钥等）
├── models.py               # 数据库模型（9张表）
├── auth.py                 # JWT 认证模块
├── requirements.txt        # Python 依赖
├── README.md               # 本文件
├── .gitignore
├── routes/
│   ├── routes_auth.py      # 认证接口（登录/登出/当前用户）
│   ├── routes_employee.py  # 员工管理接口
│   ├── routes_appraisal.py # 考核管理接口
│   └── routes_metric.py    # 业务指标接口
└── static/                 # 前端页面
    ├── login.html          # 登录页
    ├── dashboard.html     # 工作台
    ├── employees.html     # 员工管理
    ├── metrics.html       # 业务指标
    ├── data-entry.html    # 数据录入
    ├── appraisal-cycle.html    # 考核周期
    ├── appraisal-template.html # 考核模板
    ├── appraisal-list.html    # 考核列表
    ├── appraisal-form.html    # 考核详情/评分
    └── reports.html        # 报表中心
```

---

## 考核流程

1. **HR 创建考核周期** → 设置自评/上级评分时间段
2. **HR 创建考核模板** → 配置考核指标和权重
3. **HR 批量生成考核单** → 指定周期 + 员工
4. **员工自评** → 填写各指标得分和说明
5. **上级评分** → 经理查看下属考核单并评分
6. **系统计算最终得分** → 加权汇总

---

## 数据库模型（9张表）

| 表名 | 说明 |
|------|------|
| User | 系统用户（账号/密码/角色） |
| Department | 部门 |
| Employee | 员工档案 |
| BusinessMetric | 业务指标定义 |
| AppraisalTemplate | 考核模板 |
| AppraisalCycle | 考核周期 |
| Appraisal | 考核单 |
| BusinessData | 业务数据录入 |
| AchievementRule | 达成规则配置 |

---

## API 接口概览

```
POST   /api/auth/login           登录
GET    /api/auth/current-user    当前用户
PUT    /api/auth/change-password 修改密码

GET    /api/employee/list        员工列表
POST   /api/employee/create      创建员工
PUT    /api/employee/<id>       更新员工
DELETE /api/employee/<id>       删除员工
GET    /api/employee/departments 部门列表

GET    /api/appraisal/cycles           考核周期列表
POST   /api/appraisal/cycles           创建周期
GET    /api/appraisal/templates        模板列表
POST   /api/appraisal/templates        创建模板
GET    /api/appraisal/list             考核单列表
POST   /api/appraisal/batch-create     批量创建考核单
POST   /api/appraisal/<id>/self-assessment    提交自评
POST   /api/appraisal/<id>/manager-review    提交上级评分

GET    /api/metric/metrics       指标列表
POST   /api/metric/metrics       创建指标
GET    /api/metric/data           业务数据列表
POST   /api/metric/data           录入业务数据
POST   /api/metric/data/batch    批量录入
GET    /api/metric/statistics    统计报表
```

---

## 权限说明

| 角色 | 可操作范围 |
|------|-----------|
| admin（管理员） | 全部功能 |
| manager（经理） | 本部门下属员工管理、评分 |
| employee（员工） | 仅查看和自评本人考核单 |

---

## 演示数据

系统首次启动时自动初始化：

- **部门**: 技术部 / 销售部 / 人事部 / 运营部
- **员工**: 6人（张明、王芳、李华、赵强、周莉、吴涛）
- **指标**: 销售额(30%) / 客户满意度(25%) / 产品上架率(20%) / 客户回购率(15%) / 团队协作(10%)
- **周期**: 2026年Q3绩效考核（进行中）
- **考核单**: 6名员工各1条待考核记录

---

## 部署方式

### 方式一：直接运行（推荐开发/小规模）

```bash
pip install -r requirements.txt
nohup python app.py > /tmp/pbc.log 2>&1 &
```

### 方式二：Gunicorn 生产部署

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

### 服务器端口配置

如需开放外网访问，请在阿里云安全组开放 TCP 8000 端口。

---

## 生产环境注意事项

- [ ] 修改 `config.py` 中的 `SECRET_KEY` 和 `JWT_SECRET_KEY`
- [ ] 修改演示账号默认密码
- [ ] 定期备份 `pbc.db` 数据库文件
- [ ] 建议使用 Nginx 反向代理 + HTTPS

---

© 2026 绿林工具 | v1.0.0
