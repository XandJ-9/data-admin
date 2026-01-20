# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Data Admin** is a unified data management and query platform combining Django + DRF backend with Vue3 + Vite frontend (RuoYi-Vue3 UI style). Core features include data source management, metadata catalog, online query execution, query auditing, and operational monitoring.

**Tech Stack:**
- Backend: Django 5.2 + DRF + SQLite/MySQL/PostgreSQL/Presto support
- Frontend: Vue 3 + Element Plus + Vite + Pinia
- Authentication: JWT (django-rest-framework-simplejwt)

## Common Development Commands

### Backend (Django with uv)

```bash
# Navigate to backend
cd backend

# Install uv (if not already installed)
# pip install uv

# Install dependencies using uv (faster than pip)
uv pip install -r requirements.txt

# Or use uv for virtual environment management
uv venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
uv pip install -r requirements.txt

# Database migrations
python manage.py migrate
python manage.py makemigrations  # Create new migrations after model changes

# Run development server
python manage.py runserver 0.0.0.0:8000

# Initialize system data (admin user, roles, menus)
python manage.py init_system

# Test specific module
python manage.py test apps.system

# Add new package
uv pip install <package_name>
# Then update requirements.txt:
uv pip freeze > requirements.txt
```

### Frontend (Vue3 + Vite with pnpm)

```bash
# Navigate to frontend
cd frontend

# Install pnpm (if not already installed)
# npm install -g pnpm

# Install dependencies
pnpm install

# Development server
pnpm dev

# Production build
pnpm build:prod

# Staging build
pnpm build:stage

# Add new package
pnpm add <package_name>
pnpm add -D <dev_package_name>
```

### Production Deployment

```bash
# Build frontend
cd frontend && pnpm build:prod

# Copy build artifacts to backend (backend/dist/ serves static files)
cp -r ./dist/* ../backend/dist/

# Run backend with gunicorn (WSGI) or uvicorn (ASGI)
cd backend
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## Architecture & Code Organization

### Backend Structure

```
backend/
├── config/          # Django settings, urls, wsgi/asgi
├── apps/
│   ├── system/      # User, Role, Menu, Dept, Dict, Config, Notice, Post
│   ├── datasource/  # Data source connections, testing
│   ├── datameta/    # Metadata catalog (MetaTable, MetaColumn)
│   ├── dataservice/ # Query execution, QueryLog, InterfaceInfo
│   ├── dataintegration/ # Integration tasks
│   ├── datastudio/  # Data studio workspace
│   ├── datataskmonitor/ # Scheduled tasks
│   ├── monitor/     # Server monitoring, login logs
│   ├── dbutils/     # Database executor abstraction layer
│   ├── common/      # Base mixins, pagination, encryption
│   └── utils/       # Excel export utilities
└── manage.py
```

### Core Abstractions

**BaseModel** ([system/models.py](backend/apps/system/models.py:5))
- All models inherit from `BaseModel` for audit fields: `create_by`, `update_by`, `create_time`, `update_time`, `del_flag`
- Soft delete pattern: `del_flag='0'` (normal), `'1'` (deleted)
- Always define `Meta.db_table` and `indexes`

**BaseViewSet** ([system/views/core.py](backend/apps/system/views/core.py:21))
- Inherits from `BaseViewMixin` + `viewsets.ModelViewSet`
- Provides unified response methods: `ok()`, `error()`, `data()`, `not_found()`, `raw_response()`
- Auto-filters `del_flag='0'` in `get_queryset()`
- Uses `@audit_log` decorator for create/update operations
- Standard list response: `{code: 200, msg: '...', rows: [...], total: N}`

**DataSourceExecutor** ([dbutils/base.py](backend/apps/dbutils/base.py:5))
- Abstract base for database operations across SQLite/MySQL/PostgreSQL/Presto
- Key methods: `execute_query()`, `list_tables()`, `get_table_schema()`, `get_table_info()`, `list_tables_info()`
- SQL safety: `_check_sql()` only allows SELECT/WITH/SHOW/DESCRIBE/EXPLAIN
- Auto-pagination via `build_pagination_sql()`

**Executor Factory** ([dbutils/factory.py](backend/apps/dbutils/factory.py:7))
- `get_executor(info)` routes to appropriate executor based on `type` field
- Supported types: `sqlite`, `mysql`, `mariadb`, `starrocks`, `postgres`, `postgresql`, `presto`, `trino`

### Frontend Structure

```
frontend/src/
├── api/             # API wrappers for each module (datasource.js, datameta.js, etc.)
├── components/      # Reusable components (Editor, Pagination, IconSelect, etc.)
├── views/           # Page components organized by module
├── router/          # Vue Router configuration (auto-generated from backend)
├── store/           # Pinia state modules (user, permission, dict, settings)
├── utils/           # Request interceptor, auth, dict utils
├── directive/       # Custom directives (hasPermi, hasRole)
├── layout/          # Layout components (sidebar, header)
└── main.js          # App entry point
```

## Key Patterns & Conventions

### REST API Patterns

- List: `GET /module/` with `pageNum`, `pageSize` query params
- Detail: `GET /module/{id}/`
- Create: `POST /module/` with request body
- Update: `PUT /module/{id}/` (also supports bulk update via PUT `/module/` with body containing IDs)
- Delete: `DELETE /module/{id}/` (soft delete via `del_flag`, supports comma-separated IDs)
- Custom actions: `@action(detail=True|False, methods=['post'], url_path='path')`

### Response Format

All endpoints return structured JSON:
- Success: `{code: 200, msg: 'message', data: {...}}` or `{code: 200, rows: [...], total: N, msg: '...'}`
- Error: `{code: 400|404|500, msg: 'error message'}`

### Serialization: Camel Case Output

- Serializers inherit `BaseModelSerializer` which auto-converts snake_case to camelCase
- Example: `create_by` → `createBy`, `update_time` → `updateTime`
- Input parameters from frontend use camelCase (e.g., `dataSourceId`, `pageNum`)

### Authentication & Authorization

- JWT via `django-rest-framework-simplejwt`
- Permission classes: `[IsAuthenticated, HasRolePermission]`
- Role-based: Set `required_roles = ['role_key']` on ViewSet
- Admin role (`admin`) bypasses all permission checks

### Database Queries

For data source queries, use the executor abstraction:
```python
from apps.dbutils.factory import get_executor

info = {'type': 'mysql', 'host': '...', 'port': 3306, ...}
executor = get_executor(info)
result = executor.execute_query(sql, params=None, page_size=10, offset=0)
# Returns: {"columns": [...], "rows": [[...]], "next": {...}|None}
```

### Metadata Collection Pattern

When collecting metadata from a data source:
1. Use `list_tables_info()` to get table metadata
2. For each table, call `get_table_schema()` to get column info
3. Create/update `MetaTable` and `MetaColumn` records
4. Soft-delete old columns (`del_flag='1'`) before re-importing
5. Field `order` (from 1) is returned in `get_table_schema()` for stable column ordering

### SQL Template Rendering

Queries support Django template syntax for parameterization:
```sql
SELECT * FROM table WHERE id={{ id }} AND name='{{ name }}'
```
Rendered server-side via `Template(sql).render(Context(params))` before execution.

## Development Guidelines

### Adding a New Data Source Type

1. Create executor in `dbutils/{type}.py` inheriting `DataSourceExecutor`
2. Implement: `connect()`, `execute_query()`, `list_tables()`, `get_table_schema()`, `get_table_info()`, `list_tables_info()`, `build_pagination_sql()`
3. Add case in `factory.py` `get_executor()` function
4. Update frontend datasource type dropdown options

### Creating a New Module

1. Create app directory under `apps/`
2. Define models inheriting `BaseModel`
3. Create serializers inheriting `BaseModelSerializer`
4. Create ViewSet inheriting `BaseViewSet`
5. Register URLs in module `urls.py` and include in `config/urls.py`
6. Run `python manage.py makemigrations && migrate`
7. Create frontend API wrapper in `src/api/{module}.js`
8. Create view component in `src/views/{module}/`

If adding new Python packages, use `uv pip install <package>` in the backend. If adding new frontend packages, use `pnpm add <package>` in the frontend.

### Frontend View Component Pattern

- Import API functions from `src/api/{module}.js`
- Use `<pagination>` component for list views
- Use `<el-dialog>` for create/edit forms
- Use `el-table` with `:data="dataList"` for data display
- Export methods: `getList()`, `handleQuery()`, `resetQuery()`, `handleAdd()`, `handleUpdate()`, `handleDelete()`

## Important File Locations

- Backend settings: [backend/config/settings.py](backend/config/settings.py)
- Main URL routing: [backend/config/urls.py](backend/config/urls.py)
- Base models: [backend/apps/system/models.py](backend/apps/system/models.py)
- Base viewset: [backend/apps/system/views/core.py](backend/apps/system/views/core.py)
- Executor interface: [backend/apps/dbutils/base.py](backend/apps/dbutils/base.py)
- Executor factory: [backend/apps/dbutils/factory.py](backend/apps/dbutils/factory.py)
- Frontend router: [frontend/src/router/index.js](frontend/src/router/index.js)
- API request wrapper: [frontend/src/utils/request.js](frontend/src/utils/request.js)
- Environment configs: [frontend/.env.*](frontend/.env.development)

## Environment Configuration

- Backend: Uses `backend/db.sqlite3` by default. Configure MySQL/PostgreSQL in `config/settings.py` `DATABASES`
- Frontend dev: API proxy at `/dev-api` → `http://localhost:8000/data-api` (see [vite.config.js](frontend/vite.config.js))
- Frontend prod: Base URL `/data-admin/`, API `/data-api` (see [.env.production](frontend/.env.production))
