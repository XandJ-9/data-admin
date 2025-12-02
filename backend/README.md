# 后端（Django + DRF）

## 概述
后端提供系统管理（用户、角色、菜单、字典、参数）、数据源管理、查询执行与查询日志记录能力。接口采用统一响应格式与软删除策略，支持 JWT 认证与 drf-spectacular 文档。

## 目录结构
- `config/`：项目配置（`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`）
- `apps/system/`：系统模块（模型、序列化器、视图、路由）
- `apps/datasource/`：数据源与查询日志模块
- `apps/dbutils/`：统一查询执行器（SQLite/MySQL/Postgres）
- `pyproject.toml`：依赖通过 `uv` 管理（Python >= 3.12）

## 关键能力
- 认证与权限：JWT（`simplejwt`）、基础 RBAC（角色/菜单）
- 路由生成：后端根据菜单生成前端路由树（`GET /getRouters`）
- 系统管理：用户、角色、菜单、字典、参数配置
- 数据源管理：CRUD、连通性测试（`POST /datasource/{id}/test`）
- 查询执行：`POST /datasource/{id}/query`，支持 Django 模板语法（`{sql, params}`）
- 查询日志：`GET /datasource/query-log`，记录时间、用户、渲染后 SQL、状态、耗时与错误
- 文档：drf-spectacular（可启用 `/api/schema` 与 `/api/docs`）

## 统一约定
- 响应：成功 `{ code:200, msg, data }`，列表 `{ rows, total }`
- 软删除：含 `del_flag` 的模型统一软删（值 `'1'`）
- 审计字段：`create_by/update_by/create_time/update_time`
- 安全：敏感信息不返回；密码加密存储（`apps/common/encrypt.py`）

## 运行与开发
1. 创建或激活虚拟环境（推荐在 `backend/.venv`）
   - `python -m venv .venv`
   - `./.venv/Scripts/activate`
2. 安装依赖（推荐 uv）
   - `uv pip sync pyproject.toml`
   或使用 pip：`pip install -r requirements.txt`
3. 迁移与启动
   - `python manage.py migrate`
   - `python manage.py runserver 0.0.0.0:8000`

## 主要接口
- 路由树：`GET /getRouters`
- 数据源：`/datasource/`（REST 风格）
- 查询执行：`POST /datasource/{id}/query`
- 查询日志：`GET /datasource/query-log`

## 注意事项
- 使用 Python 3.12 及以上版本
- 数据源类型通过 `db_type` 指定（`sqlite`、`mysql/mariadb`、`postgres/postgresql`）
- SQL 查询支持模板语法，仅用于渲染 SQL 文本，不参与数据库参数绑定


