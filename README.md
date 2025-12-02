# Data Admin（前后端分离）



## 一、总体概览
该仓库是一个前后端分离的数据管理与查询平台，包含两个主要子项目：
- `backend/`：后端（Django + DRF）
- `frontend/`：前端（Vue 3 + Vite，基于 RuoYi-Vue3 适配）

核心能力：系统管理（用户/角色/菜单等）、数据源管理（多类型数据库）、查询执行（支持 Django 模板语法）、查询日志记录（含错误信息与耗时）。

根目录（部分）
- `.git/`, `.gitignore`
- `.python-version`, `.venv/`（存在）
- `db.sqlite3`（SQLite 数据库文件，位于根或 backend 下）
- `backend/`（后端 Django 项目）
- `frontend/`（前端 Vue + Vite 项目）
- 以及若干顶级配置或文档文件（如根 README）

## 二、后端（backend）
路径：`backend/`

主要内容
- `config/`：项目配置（settings、urls、wsgi、asgi）
- `apps/system/`：系统模块（用户、角色、菜单、字典、参数）
- `apps/datasource/`：数据源与查询日志（模型、视图、序列化器、路由）
- `apps/datasource_executor/`：统一查询执行器（根据 `db_type` 选择 SQLite/MySQL/Postgres 实现）
- `pyproject.toml`：依赖由 `uv` 管理（Python >= 3.12）

技术栈与要点
- Django 5.x + DRF，JWT 认证（simplejwt）
- drf-spectacular 文档生成
- 统一响应：`{ code, msg, data }`；列表 `{ rows, total }`
- 审计与软删：`create_by/update_by/create_time/update_time` 与 `del_flag`

运行命令（PowerShell/cmd）
1. 创建或激活虚拟环境
   - `python -m venv backend/.venv`
   - `backend/.venv/Scripts/activate`
2. 安装依赖（推荐 uv）
   - `uv pip sync backend/pyproject.toml`
   或使用 pip：`pip install -r backend/requirements.txt`
3. 迁移与启动
   - `python backend/manage.py migrate`
   - `python backend/manage.py runserver 0.0.0.0:8000`

## 三、前端（frontend）
路径：`frontend/`

主要内容与特性
- 基于 RuoYi-Vue3 封装的管理后台
- 新增数据源管理、数据查询、查询日志等页面
- 结果列表列宽自适应与溢出 tooltip 展示

开发服务器
- 端口：`vite.config.js` 配置为 `80`
- 代理：`/dev-api` → `http://localhost:8000`

运行命令（PowerShell/cmd）
1. 安装依赖：`npm install`
2. 启动开发：`npm run dev`
3. 构建：`npm run build:prod` / `npm run build:stage`

## 四、关键文件与作用（快速索引）
- `backend/manage.py`：Django 管理命令入口（运行服务器、迁移等）
- `backend/pyproject.toml`：项目元信息（Python 版本等）
- `backend/requirements.txt`：后端依赖
- `backend/config/`：Django 项目配置（settings, urls）
- `backend/apps/system/`：系统业务模块
- `backend/apps/datasource/`：数据源与查询日志模块
- `frontend/package.json`：前端依赖与脚本
- `frontend/index.html`：前端入口 HTML（Vite dev server 会提供）
- `bin/*.bat`：项目提供的 Windows 批处理脚本（构建/运行等）

## 五、本地运行
在 Windows（cmd.exe）上
1. 后端（Python/Django）
   - cd backend
   - python -m venv .venv 或使用现有 `backend/.venv`
   - .venv\Scripts\activate
   - uv pip sync pyproject.toml 或 pip install -r requirements.txt
   - python manage.py migrate
   - python manage.py runserver 0.0.0.0:8000
2. 前端（Vite）
   - cd frontend
   - npm install
   - npm run dev
3. 在开发阶段，前端端口为 80，通过 `/dev-api` 代理到后端 8000。

## 六、注意事项与规范
- 后端 `pyproject.toml` 声明 Python >=3.12，请使用匹配版本的 Python 环境。
- 统一响应与软删、审计字段遵循后端 `BaseViewSet` 约定
- 严禁泄露敏感信息；密码字段加密存储
- 如需接口文档，请启用 drf-spectacular 并访问 `/api/docs`

