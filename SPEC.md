# 绿林工具绩效管理系统 - 技术规格书

## 1. 概念与愿景

新一代绩效管理系统，采用微软 Fluent Design 设计语言，界面简洁专业，操作流畅直观。系统围绕 PBC（Personal Business Commitment）考核体系，帮助企业实现目标对齐、过程跟踪、结果评估的闭环管理。

## 2. 设计语言

### 视觉风格
- **风格**: Microsoft Fluent Design System
- **主色**: #0078D4 (Microsoft Blue)
- **强调色**: #107C10 (Green), #FF8C00 (Orange)
- **背景色**: #FFFFFF, #F3F2F1, #FAFAFA
- **文字色**: #323130 (Primary), #605E5C (Secondary)

### 字体
- 主字体: Segoe UI Variable, Segoe UI, Microsoft YaHei
- 标题: Semibold 28-52px
- 正文: Regular 16px, 行高 1.6
- 辅助: 14px

### 间距系统
- 网格: 12列
- 间距: 8px, 16px, 24px, 32px
- 卡片圆角: 8px
- 按钮圆角: 4px

### 动效
- 过渡: 200ms ease-in-out
- 悬停: scale 0.98, 颜色加深
- 加载: 骨架屏

## 3. 布局结构

### 登录页
- 左侧品牌区: 渐变背景 + 功能特性展示
- 右侧登录区: Logo + 表单 + 角色切换

### 工作台
- 顶部导航: Logo + 菜单 + 搜索 + 通知 + 用户
- 侧边栏: 导航菜单（可折叠）
- 主内容区: 仪表盘/列表/详情

## 4. 功能模块

### 4.1 认证模块
- 用户登录/退出
- 角色切换（HR管理员/部门经理/员工）
- 记住登录状态

### 4.2 工作台/仪表盘
- 欢迎信息 + 快捷操作
- 待办事项卡片
- 考核进度概览
- 近期动态

### 4.3 员工管理
- 员工列表（搜索/筛选）
- 员工详情
- 新增/编辑员工
- 部门管理

### 4.4 业务指标管理
- 指标库
- 指标分类（量化/非量化）
- 指标配置（权重、目标值）

### 4.5 数据录入
- 录入界面
- 录入记录列表
- 审核状态

### 4.6 考核模板
- 模板列表
- 模板详情/编辑
- 模板与指标关联

### 4.7 考核周期
- 周期列表
- 周期详情（开始/结束时间）
- 周期状态管理

### 4.8 考核单
- 考核单列表
- 考核单详情（员工自评 + 上级评分）
- 考核进度跟踪
- 最终得分计算

### 4.9 考核结果
- 结果汇总
- 导出功能
- 历史查询

## 5. 权限体系

| 角色 | 权限 |
|------|------|
| HR管理员 | 全权限：员工管理、模板管理、周期管理、数据查看、结果导出 |
| 部门经理 | 本部门员工管理、考核打分、结果查看 |
| 员工 | 自评、数据录入、查看自己考核结果 |

## 6. 技术架构

### 后端
- 框架: Flask
- 数据库: MariaDB (已有)
- ORM: SQLAlchemy
- 认证: JWT

### 前端
- HTML5 + CSS3 + JavaScript
- 无框架依赖（轻量可控）
- Fetch API 调用后端

### 部署
- WSGI: Gunicorn
- 服务器: 阿里云 Ubuntu
- 端口: 8000

## 7. 数据模型

### 员工表 (employee)
- id, employee_no, name, department, position, manager_id, status, created_at

### 业务指标表 (business_metric)
- id, code, name, type(量化/非量化), unit, weight, description

### 考核模板表 (appraisal_template)
- id, name, description, metrics(JSON), created_by, created_at

### 考核周期表 (appraisal_cycle)
- id, name, start_date, end_date, status, created_at

### 考核单表 (appraisal)
- id, cycle_id, employee_id, status, self_assessment(JSON), manager_score(JSON), final_score, created_at

### 业务数据表 (business_data)
- id, employee_id, metric_id, period, value, target, recorded_by, recorded_at

### 用户表 (user)
- id, username, password_hash, role, employee_id, created_at

## 8. 评分规则

### 量化指标
- 达成系数 = 实际值 / 目标值
- 得分 = 达成系数 × 权重 × 100
- 封顶规则：不同指标可设置不同上限（1.0 或更高）

### 非量化指标
- 0-100分制
- 员工自评(参考) + 上级最终评分

### 最终得分
- 各指标加权求和
- 100分满分制
