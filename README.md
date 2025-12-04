# Data Admin 项目说明文档

> 一体化数据管理与查询平台，后端基于 Django + DRF，前端基于 Vue3 + Vite，适配 RuoYi-Vue3 风格与权限体系。本文档面向开发者与贡献者，提供项目概览、功能说明、目录结构、核心抽象层设计、快速上手与开发规范指引。



## 项目概览

- 后端：Django + Django REST Framework（DRF）
- 前端：Vue 3 + Element Plus + Vite（适配 RuoYi-Vue3）
- 数据库：默认 SQLite（可扩展 MySQL / PostgreSQL）
- 目标：统一管理数据源、元数据采集、在线数据查询、查询日志审计、系统与权限管理、运维监控等。



## 功能特性

- 系统管理
  - 用户与角色、菜单与权限、登录日志、操作日志
  - 字典、参数、通知公告等通用功能
- 数据源管理
  - 支持 SQLite / MySQL / PostgreSQL 的连接测试、配置管理
  - 统一查询执行器，限定只允许查询类语句（SELECT/WITH/SHOW/DESCRIBE/EXPLAIN）
- 数据查询
  - 支持分页、参数化查询、Django 模板语法（语法高亮在前端 Editor 中实现）
  - 查询日志记录（语句、数据源、耗时、执行人等）
- 元数据管理
  - 按数据源采集/更新表级与字段级元数据
  - 字段序号 `order`（从 1 开始）统一返回并持久化，前端稳定按序展示
- 业务数据浏览
  - 列出数据源中的表、字段信息（含注释、主键、非空、默认值等）
  - 支持选择数据库（MySQL），快速查看结构
- 监控运维
  - 服务监控页面：内存、CPU、磁盘等基础指标展示（前端适配）



## 技术栈

- 后端：Django、Django REST Framework
- 前端：Vue 3、Element Plus、Vite、Pinia（RuoYi 适配）
- 数据库：SQLite / MySQL / PostgreSQL（可扩展）
- 其他：Axios（API 封装）、ESLint 配置、RuoYi 脚手架结构



## 目录结构

```
ruoyi-django/
├── README.md                 # 根 README（项目概述与启动）
├── 说明文档.md               # 本文档（统一说明）
├── chat.md                   # 模块协作与需求讨论
├── backend/                  # 后端工程（Django）
│   ├── README.md             # 后端说明与启动指引
│   ├── 开发规范.md           # 后端开发规范（约束与约定）
│   ├── apps/                 # 业务应用模块
│   │   ├── system/           # 系统管理（用户/角色/权限/日志）
│   │   ├── datasource/       # 数据源（模型/序列化/视图）
│   │   ├── datameta/         # 元数据（表/列采集与维护）
│   │   └── dbutils/          # 数据库执行器与统一接口
│   ├── config/               # Django 配置（settings/urls）
│   ├── manage.py             # Django 管理入口
│   ├── requirements.txt      # 后端依赖
│   └── db.sqlite3            # 默认开发数据库
└── frontend/                 # 前端工程（Vue3 + Vite）
    ├── README.md             # 前端说明与启动指引
    ├── src/                  # 源码
    │   ├── api/              # API 封装（datasource、datameta 等）
    │   ├── components/       # 通用组件（Editor/CodeEditor/Pagination 等）
    │   ├── views/            # 页面视图（datasource/datameta/system/monitor）
    │   ├── main.js           # 应用初始化与全局插件
    │   └── router/           # 路由与菜单
    ├── .env.*                # 环境变量配置
    ├── index.html            # 入口模板
    └── vite.config.js        # Vite 配置
```



## 核心设计与公共抽象层

### 后端

- 统一响应与基础模型
  - 所有视图继承 `BaseViewSet / BaseViewMixin`，统一 `ok / error / not_found / raw_response` 输出风格
  - 模型继承 `BaseModel`，提供通用审计字段（`create_by/update_by/create_time/update_time`）、软删除 `del_flag` 等
- 权限与认证
  - DRF `IsAuthenticated` + 自研 `HasRolePermission`，与前端 RuoYi 菜单/角色联动
- 数据库执行器（统一抽象）
  - 抽象基类：`apps/dbutils/base.py`
    ```python
    class DataSourceExecutor:
        def execute_query(self, sql, params=None, page_size=None, offset=None):
            # 只允许查询类语句，并支持自动分页（LIMIT/OFFSET）
        def _check_sql(self, sql):
            # 移除注释并校验前缀：select/with/show/describe/explain
    ```
  - 工厂选择器：`apps/dbutils/factory.py`
    ```python
    def get_executor(info):
        t = str((info or {}).get('type', '')).lower()
        if t == 'sqlite': return SqliteExecutor(info)
        if t in ('mysql','mariadb'): return MysqlExecutor(info)
        if t in ('postgres','postgresql'): return PostgresExecutor(info)
        raise ValueError('unsupported datasource type')
    ```
  - 统一入口：`apps/dbutils/__init__.py`，封装 `execute_query / list_tables / get_table_schema / get_table_info / list_tables_info / get_databases`
  - 字段顺序：各执行器的 `get_table_schema` 返回字段包含统一的 `order`（从 1 开始），并且后端列表按 `order` 正序输出
    - SQLite：`PRAGMA table_info`，按枚举顺序构造 `order`
    - MySQL：`information_schema.COLUMNS` 按 `ORDINAL_POSITION` 返回 `order`
    - PostgreSQL：`pg_attribute.attnum` 顺序返回 `order`
- 元数据采集与维护
  - 表信息：`get_table_info` 返回 `tableName/databaseName/comment/createTime/updateTime`
  - 字段信息：`get_table_schema` 返回字段及 `order/name/type/notnull/default/primary/comment`
  - 采集流程：`DatametaMixin._collect_table` 写入 `MetaTable/MetaColumn`，并记录采集/更新人
- 视图与序列化
  - `MetaColumnSerializer` 将 `order` 映射为前端展示字段 `columnIndex`
  - `MetaColumnViewSet` 默认按 `order` 正序查询，确保前端“查看列”稳定按序显示
  - `BusinessDataView.columns` 接口包含并按 `order` 排序返回，业务数据浏览字段顺序与数据源一致

### 前端

- 应用初始化：`src/main.js` 注册路由、状态、权限、全局组件与指令
- API 封装：`src/api/*.js` 基于 Axios 的请求函数，统一错误处理与分页参数
- 通用组件：`Editor/CodeEditor/Pagination` 等，与 RuoYi 风格适配
- 页面模块：
  - `views/datasource/` 数据源管理、连接测试、查询与日志
  - `views/datameta/` 元数据管理（数据总览、字段查看、增删改）、业务数据浏览
  - `views/system/` 系统管理（用户、角色、菜单等）
  - `views/monitor/` 服务监控（基础指标）
- 字段展示：
  - 元数据页面「字段信息」对话框使用 `columnIndex` 展示序号
  - 业务数据页面「查看字段」接口返回 `order`，按序展示字段结构



## 快速上手

### 后端（开发环境）

- 1）创建虚拟环境并安装依赖
  - `python -m venv .venv`
  - `source .venv/bin/activate`（macOS/Linux）或 `./.venv/Scripts/activate`（Windows）
  - `pip install -r backend/requirements.txt`
- 2）数据库迁移与启动
  - `cd backend`
  - `python manage.py migrate`
  - `python manage.py runserver 0.0.0.0:8000`
- 3）默认配置
  - 默认使用 `backend/db.sqlite3`；如需使用 MySQL/PostgreSQL，请在 `backend/config/settings.py` 中调整数据库配置

### 前端（开发环境）

- 1）安装依赖：`cd frontend && npm i`
- 2）启动开发服务：`npm run dev`
- 3）默认访问：`http://localhost:80/`（端口占用时自动切换，如 `http://localhost:81/`）
- 4）环境变量：`.env.development/.env.staging/.env.production` 可配置后端 API 基础路径、应用上下文等



## 开发规范与约定

- 统一 REST 风格与分页参数（`pageNum/pageSize`）
- 统一响应结构：`{ code, msg, data | rows, total }`
- 软删除与审计字段：模型内置 `del_flag` 与 `create_by/update_by/...`
- 输入大小写约定：统一与 RuoYi-Vue3 参数风格保持一致（如 `dataSourceId/tableName`）
- 异常处理：后端统一捕获并输出错误消息，前端统一弹窗/提示
- 权限控制：后端 `HasRolePermission` + 前端菜单/角色匹配



## 部署说明（生产环境）

### 路径与约定

- 前端基础路径：`/data-admin/`（`.env.production` 的 `VITE_APP_BASE_URL`）
- 后端 API 前缀：`/data-api`（`.env.production` 的 `VITE_APP_BASE_API`）
- 后端模板目录：`backend/config/settings.py` 中 `TEMPLATES.DIRS = [BASE_DIR/'dist']`
- 静态资源路径：`STATIC_URL = '/data-admin/static/'`，`STATICFILES_DIRS = [BASE_DIR/'dist/static']`

以上约定意味着：前端构建产物需要位于后端工程的 `backend/dist` 目录（含 `index.html` 与 `static/`）。

### 前端构建与拷贝

1）检查生产环境变量

```
# frontend/.env.production
VITE_APP_BASE_URL = '/data-admin/'
VITE_APP_BASE_API = '/data-api'
```

2）构建前端并拷贝到后端

```
cd frontend
npm install
npm run build:prod

# 将构建产物拷贝到后端（请根据你的部署目录调整）
cp -r ./dist/* ../backend/dist/
```

完成后，`backend/dist` 应包含：

- `index.html`
- `static/` 目录（JS/CSS/图片等）

### 后端服务启动（WSGI/ASGI）

- WSGI（推荐稳定方案）

```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 以 WSGI 启动
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

- ASGI（如需 WebSocket/更高并发，可选）

```
pip install uvicorn
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 2
```

> 注意：生产环境请关闭 `DEBUG` 并设置安全的 `SECRET_KEY`，以及正确配置 `ALLOWED_HOSTS`。

### Nginx 反向代理示例

假设后端服务在 `127.0.0.1:8000`，部署目录为 `/opt/data-admin`：

```
upstream data_admin_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your.domain.com;

    # 前端静态资源（由 Nginx 直接服务，性能更好）
    location /data-admin/static/ {
        alias /opt/data-admin/backend/dist/static/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # 前端入口与路由（交给后端 TemplateView 返回 index.html）
    location /data-admin/ {
        proxy_pass http://data_admin_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 后端 API
    location /data-api/ {
        proxy_pass http://data_admin_backend/data-api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

> 如果不希望后端处理前端入口，也可让 Nginx 直接返回 `index.html`，但需保证前后端的 `base` 与路由模式配置一致。

### 数据库与安全配置

- 数据库：在 `backend/config/settings.py` 调整 `DATABASES`（生产建议 MySQL/PostgreSQL）。
- 主机与域名：设置 `ALLOWED_HOSTS = ['your.domain.com', 'localhost']`。
- 秘钥与调试：生产关闭 `DEBUG`，更新 `SECRET_KEY`。
- 静态与模板：确认 `backend/dist` 存在并与前端构建产物同步。

### Docker Compose（可选示例）

项目未内置容器配置，若需快速部署可参考：

```
version: '3.8'
services:
  backend:
    build: ./backend
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./backend/dist:/app/dist
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings
    restart: always

  nginx:
    image: nginx:stable
    depends_on:
      - backend
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./backend/dist/static:/usr/share/nginx/html/data-admin/static:ro
    restart: always
```

> 构建镜像时需编写 `backend/Dockerfile`，并保证 `backend/dist` 已包含前端产物。

### 常见问题与排查

- 前端空白或 404：检查 `VITE_APP_BASE_URL` 是否为 `/data-admin/`，以及 `backend/dist/index.html` 是否存在。
- 静态资源 404：确认 Nginx 的 `alias` 路径与 `STATIC_URL` 对应，目录权限可读。
- API 404：确认 Nginx 的 `/data-api/` 代理到后端，后端 `config/urls.py` 已包含各模块路由。
- 跨域或接口错误码：生产环境下使用 `/data-api` 直连，开发环境使用代理 `/dev-api`；对照 `frontend/src/utils/request.js` 的错误处理。


## 贡献与协作

- 代码风格遵循各端既有规范；后端详见 `backend/开发规范.md`
- 提交前请运行本地开发服务并完成基本功能自检（数据源连接、查询、元数据采集与查看）
- 新增数据源类型时需实现对应执行器并注册到 `dbutils/factory.py`

## License

- 本项目遵循常见开源社区实践；前端适配 RuoYi-Vue3（MIT）。如需二次分发，请保留相关声明。

