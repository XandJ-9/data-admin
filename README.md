# Data Admin

> 一体化数据管理与查询平台，后端基于 Django + DRF，前端基于 Vue3 + Vite，适配 RuoYi-Vue3 风格与权限体系。

## 项目概览

**Data Admin** 是一个统一的数据资产管理平台，涵盖数据源管理、元数据采集、表血缘追踪、在线 SQL 查询、数据接口服务、ETL 任务编排与运维监控等核心功能，面向数据团队提供从数据接入到数据消费的全链路管理能力。

### 核心特性

- **数据源管理** — 支持 MySQL、PostgreSQL、SQLite、Presto/Trino、StarRocks 等多种数据库，提供连通性测试与连接信息加密存储
- **元数据管理** — 异步采集数据库、表、字段元数据，支持进度追踪、增量更新与元数据浏览搜索
- **表血缘追踪** — 手动配置表级上下游血缘关系，支持多层递归查询与可视化血缘图谱，辅助影响分析
- **数据查询** — 在线 SQL 执行，支持分页、Django 模板语法参数化、CSV 导出、查询日志审计
- **数据接口服务** — 将 SQL 封装为标准化数据接口，支持字段定义（输入/输出）、分页、接口元数据 Excel 导入导出
- **ETL 任务管理** — 支持 DataX / Spark SQL / 自定义 Python 执行器，提供全量/增量策略、版本管理、水位线追踪、数据质量校验
- **系统管理** — 用户、角色、部门、岗位、菜单、字典、参数配置，完整 RBAC 权限体系
- **监控运维** — 服务器状态监控（CPU/内存/磁盘）、操作审计日志、登录日志、在线用户管理

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django 5.2 + DRF 3.16 + SimpleJWT + drf-spectacular |
| 前端 | Vue 3.5 + Element Plus 2.10 + Vite 6 + Pinia + Vue Router 4 |
| 数据库 | SQLite / MySQL / PostgreSQL（平台自身），支持连接多种外部数据源 |
| 包管理 | uv（后端） + pnpm（前端） |

### 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Vue3 前端 (Vite)                    │
│  Element Plus · Pinia · 动态路由 · Ace Editor         │
├─────────────────────────────────────────────────────┤
│                Nginx / 开发代理 (Vite)                │
├─────────────────────────────────────────────────────┤
│                  Django + DRF 后端                     │
│  ┌──────────┬──────────┬──────────┬──────────┐      │
│  │ 系统管理  │ 数据资产  │ 数据服务  │  ETL    │      │
│  │ system   │dataasset │dataservice│ dataetl  │      │
│  ├──────────┴──────────┴──────────┴──────────┤      │
│  │   BaseViewSet · BaseModel · 统一响应/分页    │      │
│  ├───────────────────────────────────────────┤      │
│  │        dbutils 数据库执行器抽象层            │      │
│  │  SQLite · MySQL · PostgreSQL · Presto      │      │
│  └───────────────────────────────────────────┘      │
├─────────────────────────────────────────────────────┤
│          外部数据源 (MySQL/PG/Presto/StarRocks...)    │
└─────────────────────────────────────────────────────┘
```

## 功能模块

### 1. 数据源管理 (`datasource`)

管理外部数据库连接信息，支持多种数据库类型的统一接入。

- 数据源 CRUD，密码加密存储
- 连通性测试（按 ID 或请求体参数）
- 支持数据库类型：MySQL / MariaDB / PostgreSQL / SQLite / Presto / Trino / StarRocks / Oracle / SQL Server

### 2. 数据资产管理 (`dataasset`)

元数据采集、浏览与表血缘管理。

- **元数据采集**：异步线程采集，实时进度追踪（进度百分比/当前表/成功失败数），支持取消操作
- **元数据浏览**：按数据源、数据库、表名过滤搜索，查看表结构（字段名/类型/注释/主键/默认值）
- **表血缘**：配置上下游关系，递归查询多层血缘，生成可视化血缘图谱
- **数据总览仪表盘**：数据源/表/字段统计概览

### 3. 数据服务 (`dataservice`)

在线查询与数据接口封装。

- **SQL 查询**：在线编辑执行 SQL，自动分页，支持 Django 模板语法参数化 (`{{ param }}`)
- **CSV 导出**：查询结果一键导出（支持 BOM 编码）
- **查询日志**：记录每次查询的用户、SQL、耗时、状态、错误信息
- **数据接口管理**：将 SQL 封装为标准化接口，定义输入/输出字段（支持 15 种数据类型）
- **接口执行**：通过接口 ID 调用预定义查询
- **接口元数据导入导出**：Excel 批量管理接口定义

### 4. ETL 任务管理 (`dataetl`)

数据抽取、转换与加载的全流程管理。

- **任务定义**：配置源表/目标表、SQL 模板、字段映射与转换规则
- **执行策略**：全量（full）与增量（increment）两种模式，增量支持时间戳/ID/CDC 水位线追踪
- **执行器**：
  - `DataXExecutor` — 生成 DataX JSON 配置，管理子进程执行
  - `SparkSQLExecutor` — Spark SQL 任务提交
  - `MockExecutor` — 测试用模拟执行
- **版本管理**：任务配置快照，支持版本对比与一键回滚
- **数据质量**：空值检查、唯一性检查、范围检查、一致性检查、自定义 SQL 校验
- **执行日志**：记录每次执行的状态、耗时、处理行数、成功/失败行数

### 5. 系统管理 (`system`)

完整的后台管理功能。

- **用户管理**：用户 CRUD、密码加密、头像上传、状态管理
- **角色管理**：角色权限分配，支持 5 级数据权限（全部/自定义/本部门/本部门及以下/仅本人）
- **部门管理**：树形部门结构
- **岗位管理**：岗位信息维护
- **菜单管理**：三级菜单（目录/菜单/按钮），动态路由生成
- **字典管理**：字典类型与数据维护
- **参数配置**：系统配置键值对管理
- **通知公告**：系统通知发布

### 6. 监控管理 (`monitor`)

系统运行状态与审计。

- **服务监控**：CPU 使用率、内存统计、磁盘信息、操作系统信息
- **在线用户**：当前在线 Session 管理
- **操作日志**：业务操作审计（自动记录请求方法/URL/参数/响应/耗时）
- **登录日志**：登录记录（IP/浏览器/OS/状态/时间）

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- uv（推荐）或 pip
- pnpm

### 后端启动

```bash
cd backend

# 安装 uv（如果尚未安装）
pip install uv

# 创建虚拟环境
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
uv pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 初始化系统数据（admin 用户、角色、菜单）
python manage.py init_system

# 启动开发服务器
python manage.py runserver 0.0.0.0:8000
```

### 前端启动

```bash
cd frontend

# 安装 pnpm（如果尚未安装）
npm install -g pnpm

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 访问应用

- 前端开发地址：`http://localhost:5173`
- 后端 API 地址：`http://localhost:8000/data-api/`
- Swagger 文档：`http://localhost:8000/api/docs/`

默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`

## 项目结构

```
data-admin/
├── backend/                        # Django 后端
│   ├── apps/                      # 业务应用
│   │   ├── system/                # 系统管理（用户/角色/部门/菜单/字典/配置/通知）
│   │   │   ├── models.py          #   User, Role, Menu, Dept, Post, DictType, DictData, Config, Notice
│   │   │   ├── views/             #   BaseViewSet, 登录/登出/验证码, 路由树生成
│   │   │   └── permission.py      #   RBAC 权限控制 (HasRolePermission)
│   │   ├── datasource/            # 数据源管理
│   │   │   └── models.py          #   DataSource（连接信息 + 加密密码）
│   │   ├── dataasset/             # 数据资产管理
│   │   │   ├── models.py          #   MetaTable, MetaColumn, MetaCollectionTask, TableLineage
│   │   │   ├── collectors.py      #   异步元数据采集执行器
│   │   │   └── views.py           #   元数据浏览, 采集管理, 血缘查询
│   │   ├── dataservice/           # 数据服务
│   │   │   ├── models.py          #   QueryLog, InterfaceInfo, InterfaceField
│   │   │   ├── views.py           #   SQL 查询, CSV 导出, 接口执行
│   │   │   └── custom.py          #   自定义业务逻辑
│   │   ├── dataetl/               # ETL 任务管理
│   │   │   ├── models.py          #   ETLTask, ETLFieldMapping, ETLExecutionLog, ETLWatermark, ETLTaskTemplate, ETLQualityRule/Result
│   │   │   ├── executors/         #   执行器实现（DataX / SparkSQL / Mock）
│   │   │   └── services/          #   业务服务（任务/执行/版本/配置/监控/质量）
│   │   ├── dbutils/               # 数据库执行器抽象层
│   │   │   ├── base.py            #   DataSourceExecutor 接口定义
│   │   │   ├── factory.py         #   执行器工厂（按 db_type 路由）
│   │   │   ├── mysql.py           #   MySQL / MariaDB / StarRocks
│   │   │   ├── postgres.py        #   PostgreSQL
│   │   │   ├── presto.py          #   Presto / Trino
│   │   │   └── sqlite.py          #   SQLite
│   │   ├── monitor/               # 监控管理
│   │   │   ├── models.py          #   OperLog, Logininfor
│   │   │   └── middleware.py      #   操作日志自动记录中间件
│   │   ├── common/                # 公共组件
│   │   │   ├── mixins.py          #   BaseViewMixin（统一响应）
│   │   │   ├── util_model.py      #   BaseModel（审计字段 + 软删除）
│   │   │   ├── pagination.py      #   StandardPagination
│   │   │   ├── exceptions.py      #   统一异常处理
│   │   │   └── encrypt.py         #   密码加解密
│   │   └── utils/                 # 工具库
│   │       └── excel.py           #   Excel 导入导出
│   └── config/                    # Django 配置
│       ├── settings.py            #   REST/JWT/分页/异常处理等全局配置
│       ├── urls.py                #   路由入口（/data-api/ 前缀）
│       └── env.py                 #   数据库连接配置
├── frontend/                      # Vue3 前端
│   ├── src/
│   │   ├── api/                   # API 封装
│   │   │   ├── data/              #   datasource.js, asset.js, service.js, etl.js, meta.js
│   │   │   ├── system/            #   user.js, role.js, menu.js, dept.js, dict.js, config.js
│   │   │   └── monitor/           #   server.js, online.js, operlog.js, logininfor.js
│   │   ├── views/                 # 页面视图
│   │   │   ├── data/              #   数据模块页面
│   │   │   │   ├── datasource/    #     数据源管理
│   │   │   │   ├── asset/         #     数据资产（metadata/ + lineage/ + 仪表盘）
│   │   │   │   ├── service/       #     数据服务（query/ + interface/ + report/）
│   │   │   │   └── etl/           #     ETL 管理（任务列表/详情/执行日志）
│   │   │   ├── system/            #   系统管理页面
│   │   │   └── monitor/           #   监控管理页面
│   │   ├── store/                 #   Pinia 状态管理
│   │   ├── router/                #   路由（支持后端动态菜单生成）
│   │   ├── components/            #   通用组件
│   │   └── layout/                #   布局组件（侧边栏/头部）
│   └── vite.config.js             # Vite 构建配置
└── docs/                          # 项目文档
    ├── development-guide.md       #   开发指南
    ├── data-asset-module.md       #   数据资产模块文档
    ├── data-service-module.md     #   数据服务模块文档
    ├── data-etl-module.md         #   ETL 模块文档
    └── project-retrospective.md   #   项目复盘
```

详细的代码规范、接口设计、抽象层说明请参考各子项目文档：

- 后端：[backend/README.md](backend/README.md) — 核心抽象层、统一响应格式、REST API 规范、所有 API 端点、开发清单
- 前端：[frontend/README.md](frontend/README.md) — 技术选型、API 封装模式、页面组件模式、命名规范、开发清单

## 生产部署

### 构建前端

```bash
cd frontend
pnpm build:prod
```

### 复制到后端

```bash
mkdir -p ../backend/dist
cp -r dist/* ../backend/dist/
```

### 启动后端服务

```bash
cd backend
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /data-admin/ {
        root /path/to/backend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /data-api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 文档

| 文档 | 说明 |
|------|------|
| [development-guide.md](docs/development-guide.md) | 开发指南，包含核心抽象层、命名规范、开发模式 |
| [data-asset-module.md](docs/data-asset-module.md) | 数据资产管理模块详细文档 |
| [data-service-module.md](docs/data-service-module.md) | 数据服务模块详细文档 |
| [data-etl-module.md](docs/data-etl-module.md) | ETL 任务管理模块详细文档 |
| [project-retrospective.md](docs/project-retrospective.md) | 项目复盘记录 |

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## License

本项目遵循 MIT 许可证。前端适配 RuoYi-Vue3（MIT）。

---

**最后更新**: 2026-03-25
