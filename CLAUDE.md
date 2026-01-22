# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Data Admin** is a unified data management and query platform combining Django + DRF backend with Vue3 + Vite frontend (RuoYi-Vue3 UI style). Core features include data source management, metadata catalog, online query execution, query auditing, and operational monitoring.

**Tech Stack:**
- Backend: Django 5.2 + DRF + SQLite/MySQL/PostgreSQL/Presto support
- Frontend: Vue 3 + Element Plus + Vite + Pinia
- Authentication: JWT (django-rest-framework-simplejwt)
- **Package Managers:**
  - Backend Python: **uv** (fast Python package installer & resolver)
  - Frontend Node.js: **pnpm** (fast, disk space efficient package manager)

## Common Development Commands

### Backend (Django with uv)

**IMPORTANT:** This project uses **uv** as the Python package manager. Always use `uv` commands instead of `pip`.

```bash
# Navigate to backend
cd backend

# Install uv (if not already installed)
# pip install uv

# Create virtual environment with uv (recommended)
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies using uv (much faster than pip)
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

# Add new package - use uv, NOT pip
uv pip install <package_name>
# Then update requirements.txt:
uv pip freeze > requirements.txt
```

### Frontend (Vue3 + Vite with pnpm)

**IMPORTANT:** This project uses **pnpm** as the Node.js package manager. Always use `pnpm` commands instead of `npm` or `yarn`.

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

# Add new package - use pnpm, NOT npm or yarn
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
- Model pattern:
  ```python
  class MyModel(BaseModel):
      field_name = models.CharField(max_length=100, verbose_name='Field Name')

      class Meta:
          db_table = 'my_model'
          indexes = [
              models.Index(fields=['del_flag']),
              models.Index(fields=['field_name']),
          ]
  ```

**BaseViewSet** ([system/views/core.py](backend/apps/system/views/core.py:21))
- Inherits from `BaseViewMixin` + `viewsets.ModelViewSet`
- Auto-filters `del_flag='0'` in `get_queryset()`
- Uses `@audit_log` decorator for create/update/delete operations
- Supports bulk delete (comma-separated IDs in URL)
- Standard CRUD responses:
  - List: `{code: 200, rows: [...], total: N, msg: '操作成功'}`
  - Create/Update/Delete: `{code: 200, msg: '操作成功'}`
  - Retrieve: `{code: 200, msg: '操作成功', data: {...}}`
  - Not found: `{code: 404, msg: '未找到'}`
  - Error: `{code: 400, msg: 'error message'}`

**BaseViewMixin** ([common/mixins.py](backend/apps/common/mixins.py:6))
- Provides unified response methods:
  - `ok(msg='操作成功')` - Success response
  - `error(msg='操作失败')` - Error response
  - `data(data, msg='操作成功')` - Data response
  - `not_found(msg='未找到')` - 404 response
  - `raw_response(data)` - Raw response
  - `csv_response(columns, rows, filename, bom=False)` - CSV export
  - `excel_response(filename, workbook)` - Excel export
- ExportExcelMixin: Adds `@action(detail=False, methods=['post'])` export endpoint

**BaseModelSerializer** ([system/serializers.py](backend/apps/system/serializers.py:17))
- Auto-converts snake_case to camelCase for API responses
- Auto-includes common audit fields: `createBy`, `updateBy`, `createTime`, `updateTime`, `remark`, `status`
- Field naming: Use `source` parameter to map model fields to camelCase
  ```python
  class MySerializer(BaseModelSerializer):
      customField = serializers.CharField(source='custom_field')

      class Meta:
          model = MyModel
          fields = ['id', 'customField', 'status', 'createTime']
  ```

**CamelCaseModelSerializer** ([system/serializers.py](backend/apps/system/serializers.py:5))
- Base serializer that auto-converts all snake_case keys to camelCase
- Set `camelize = False` to disable for specific serializers

**Pagination** ([common/pagination.py](backend/apps/common/pagination.py:5))
- `StandardPagination` class with `pageNum`/`pageSize` query parameters
- Pagination is optional: only applies if `pageNum` or `pageSize` is provided
- Response format: `{code: 200, total: N, pageNum: X, pageSize: Y, rows: [...], msg: '操作成功'}`
- Max page size: 100 records

**Permission System** ([system/permission.py](backend/apps/system/permission.py:5))
- `HasRolePermission` - Role-based access control
- Set `required_roles = ['role_key']` on ViewSet
- Admin role (`admin`) bypasses all permission checks
- Usage:
  ```python
  class MyViewSet(BaseViewSet):
      required_roles = ['admin', 'editor']
  ```

**DataSourceExecutor** ([dbutils/base.py](backend/apps/dbutils/base.py:5))
- Abstract base for database operations across SQLite/MySQL/PostgreSQL/Presto
- Key methods:
  - `execute_query(sql, params=None, page_size=10, offset=0)` - Safe SQL execution with pagination
  - `list_tables()` - List all tables
  - `get_table_schema(table_name)` - Get column information
  - `get_table_info(table_name)` - Get table metadata
  - `list_tables_info()` - List all tables with metadata
- SQL safety: `_check_sql()` only allows SELECT/WITH/SHOW/DESCRIBE/EXPLAIN
- Auto-pagination via `build_pagination_sql()`

**Executor Factory** ([dbutils/factory.py](backend/apps/dbutils/factory.py:7))
- `get_executor(info)` routes to appropriate executor based on `type` field
- Supported types: `sqlite`, `mysql`, `mariadb`, `starrocks`, `postgres`, `postgresql`, `presto`, `trino`

### Frontend Structure

```
frontend/src/
├── api/             # API wrappers for each module (datasource.js, datameta.js, etc.)
├── components/      # Reusable components
│   ├── Pagination/  # Standard pagination component
│   ├── Editor/      # Code editor (Monaco)
│   ├── FileUpload/  # File upload component
│   ├── ImageUpload/ # Image upload component
│   ├── IconSelect/  # Icon selector
│   ├── DictTag/     # Dictionary tag display
│   ├── Breadcrumb/  # Breadcrumb navigation
│   ├── RightToolbar/ # Table toolbar (search, refresh, columns)
│   ├── SelectForm/  # Multi-condition search form
│   ├── CodeEditor/  # SQL code editor
│   └── FieldMapping/ # Field mapping component
├── views/           # Page components organized by module
├── router/          # Vue Router configuration (auto-generated from backend)
├── store/           # Pinia state modules (user, permission, dict, settings)
├── utils/           # Request interceptor, auth, dict utils
├── directive/       # Custom directives (hasPermi, hasRole)
├── layout/          # Layout components (sidebar, header)
└── main.js          # App entry point
```

**Key Frontend Components:**

- **Pagination** ([components/Pagination](frontend/src/components/Pagination/index.vue))
  - Props: `total`, `page`, `limit`, `pageSizes`, `layout`
  - Emits: `pagination` event with `{page, limit}`
  - Auto-scrolls to top on page change

- **API Request** ([utils/request.js](frontend/src/utils/request.js:1))
  - Axios-based with interceptors
  - Auto-injects JWT token via `Authorization: Bearer <token>`
  - Handles 401 (redirect to login), 500 (error message), 601 (warning)
  - Prevents duplicate submissions (1-second interval)
  - Download method: `download(url, params, filename, config)`

- **Pinia Store** ([store/modules/user.js](frontend/src/store/modules/user.js:8))
  - `useUserStore`: Manages user state (token, roles, permissions)
  - Actions: `login()`, `getInfo()`, `logOut()`
  - Auto-updates avatar URL with base API path
  - Default role: `ROLE_DEFAULT` if no roles assigned

## Key Patterns & Conventions

### Naming Conventions

- **Backend Models/Database**: snake_case (`user_name`, `create_time`)
- **Backend Python**: snake_case for functions/variables
- **API Responses (JSON)**: camelCase (`userName`, `createTime`)
- **Frontend Components**: PascalCase (`UserList`, `DataSourceForm`)
- **Frontend Files**: kebab-case (`user-list.vue`, `api-datasource.js`)
- **Frontend Props/Methods**: camelCase (`handleQuery`, `dataList`)

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
6. Run `python manage.py makemigrations && python manage.py migrate`
7. Create frontend API wrapper in `src/api/{module}.js`
8. Create view component in `src/views/{module}/`

**Package Installation:**
- **Backend Python packages:** Use `uv pip install <package>` (NOT `pip install`)
- **Frontend Node.js packages:** Use `pnpm add <package>` (NOT `npm install` or `yarn add`)

### Frontend View Component Pattern

- Import API functions from `src/api/{module}.js`
- Use `<pagination>` component for list views
- Use `<el-dialog>` for create/edit forms
- Use `el-table` with `:data="dataList"` for data display
- Export methods: `getList()`, `handleQuery()`, `resetQuery()`, `handleAdd()`, `handleUpdate()`, `handleDelete()`
- Standard template structure:
  ```vue
  <template>
    <div class="app-container">
      <!-- Search form -->
      <el-form :model="queryParams" ref="queryRef" :inline="true">
        <!-- Search fields -->
        <el-form-item>
          <el-button type="primary" @click="handleQuery">搜索</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- Table toolbar -->
      <right-toolbar @queryTable="getList" />

      <!-- Data table -->
      <el-table :data="dataList">
        <!-- Columns -->
        <el-table-column label="操作" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-button link @click="handleUpdate(scope.row)">修改</el-button>
            <el-button link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <pagination
        :total="total"
        v-model:page="queryParams.pageNum"
        v-model:limit="queryParams.pageSize"
        @pagination="getList"
      />

      <!-- Dialog -->
      <el-dialog v-model="open" :title="title">
        <el-form :model="form" ref="formRef">
          <!-- Form fields -->
        </el-form>
        <template #footer>
          <el-button @click="cancel">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </template>
      </el-dialog>
    </div>
  </template>
  ```

### Backend ViewSet Patterns

- Standard CRUD operations inherited from `BaseViewSet`
- Custom actions use `@action(detail=True|False, methods=['get'|'post'|'put'|'delete'], url_path='path')`
- For different serializers per operation:
  - `create_serializer_class` - Used for POST
  - `update_serializer_class` - Used for PUT/PATCH
  - `retrieve_serializer_class` - Used for GET detail
- Bulk update support: Set `update_body_serializer_class` and `update_body_id_field`
- Export support: Mix in `ExportExcelMixin` and define `export_field_label` or `export_fields` + `export_headers`

### Common Code Patterns

**ViewSet with all features:**
```python
from apps.system.views.core import BaseViewSet
from apps.common.mixins import ExportExcelMixin
from apps.system.permission import HasRolePermission
from rest_framework.permissions import IsAuthenticated

class MyViewSet(ExportExcelMixin, BaseViewSet):
    queryset = MyModel.objects.all().order_by('-create_time')
    serializer_class = MySerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    required_roles = ['admin']

    # For export functionality
    export_field_label = OrderedDict([
        ('field1', 'Field 1 Label'),
        ('field2', 'Field 2 Label'),
    ])
    export_filename = 'my_export'

    # For different serializers
    create_serializer_class = MyCreateSerializer
    update_serializer_class = MyUpdateSerializer

    # Custom action
    @action(detail=True, methods=['post'], url_path='custom-action')
    def custom_action(self, request, pk=None):
        obj = self.get_object()
        # Custom logic
        return self.data({'result': 'success'})
```

**Frontend API pattern:**
```javascript
import request from '@/utils/request'

// List with pagination
export function listData(query) {
  return request({
    url: '/module/list',
    method: 'get',
    params: query
  })
}

// Get detail
export function getData(id) {
  return request({
    url: '/module/' + id,
    method: 'get'
  })
}

// Create
export function addData(data) {
  return request({
    url: '/module',
    method: 'post',
    data: data
  })
}

// Update
export function updateData(data) {
  return request({
    url: '/module',
    method: 'put',
    data: data
  })
}

// Delete
export function delData(id) {
  return request({
    url: '/module/' + id,
    method: 'delete'
  })
}

// Custom action
export function customAction(id, data) {
  return request({
    url: '/module/' + id + '/custom-action',
    method: 'post',
    data: data
  })
}
```

## Important File Locations

### Backend
- **Settings**: [backend/config/settings.py](backend/config/settings.py) - Django settings, DRF config, DB config
- **URL routing**: [backend/config/urls.py](backend/config/urls.py) - Main URL configuration
- **Base models**: [backend/apps/system/models.py](backend/apps/system/models.py) - BaseModel definition
- **Base viewset**: [backend/apps/system/views/core.py](backend/apps/system/views/core.py) - BaseViewSet, BaseViewMixin
- **Base serializers**: [backend/apps/system/serializers.py](backend/apps/system/serializers.py) - BaseModelSerializer
- **Mixins**: [backend/apps/common/mixins.py](backend/apps/common/mixins.py) - BaseViewMixin, ExportExcelMixin
- **Pagination**: [backend/apps/common/pagination.py](backend/apps/common/pagination.py) - StandardPagination
- **Permissions**: [backend/apps/system/permission.py](backend/apps/system/permission.py) - HasRolePermission
- **Executor interface**: [backend/apps/dbutils/base.py](backend/apps/dbutils/base.py) - DataSourceExecutor
- **Executor factory**: [backend/apps/dbutils/factory.py](backend/apps/dbutils/factory.py) - get_executor()

### Frontend
- **Router**: [frontend/src/router/index.js](frontend/src/router/index.js) - Vue Router config
- **API request**: [frontend/src/utils/request.js](frontend/src/utils/request.js) - Axios config with interceptors
- **User store**: [frontend/src/store/modules/user.js](frontend/src/store/modules/user.js) - User state management
- **Auth utils**: [frontend/src/utils/auth.js](frontend/src/utils/auth.js) - Token management
- **Main entry**: [frontend/src/main.js](frontend/src/main.js) - App initialization
- **Environment configs**:
  - Development: [frontend/.env.development](frontend/.env.development)
  - Production: [frontend/.env.production](frontend/.env.production)
  - Staging: [frontend/.env.staging](frontend/.env.staging)

### Common Directories
- Backend apps: [backend/apps/](backend/apps/) - All Django apps
- Backend common: [backend/apps/common/](backend/apps/common/) - Shared utilities
- Frontend API: [frontend/src/api/](frontend/src/api/) - API wrappers by module
- Frontend components: [frontend/src/components/](frontend/src/components/) - Reusable components
- Frontend views: [frontend/src/views/](frontend/src/views/) - Page components

## Environment Configuration

### Backend
- **Default database**: `backend/db.sqlite3` (SQLite)
- **Configure MySQL/PostgreSQL**: Edit `config/settings.py` → `DATABASES` section
- **Secret key**: Generate new `SECRET_KEY` for production
- **Debug mode**: Set `DEBUG = False` in production
- **Allowed hosts**: Configure `ALLOWED_HOSTS` for production domain

### Frontend
- **Development**:
  - API proxy: `/dev-api` → `http://localhost:8000/data-api` (configured in [vite.config.js](frontend/vite.config.js))
  - Base URL: `/`
  - Hot reload enabled
- **Production**:
  - Base URL: `/data-admin/`
  - API: `/data-api`
  - Static files served from Django `backend/dist/`
- **Staging**:
  - Similar to production with staging-specific endpoints

## Development Workflow

### Creating a Complete Feature (Backend + Frontend)

**1. Backend Setup:**
```bash
cd backend
# Create Django app
python manage.py startapp mymodule apps/mymodule

# Define models in apps/mymodule/models.py
# Create serializers in apps/mymodule/serializers.py
# Create ViewSets in apps/mymodule/views.py
# Create URLs in apps/mymodule/urls.py

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Register URLs in config/urls.py
```

**2. Frontend Setup:**
```bash
cd frontend
# Create API wrapper in src/api/mymodule.js
# Create view component in src/views/mymodule/
# Add route configuration if needed
```

**3. Testing:**
- Backend: `python manage.py test apps.mymodule`
- Frontend: `pnpm dev` and access at http://localhost:5173

### Common Gotchas

1. **Serializer Field Mapping**: Always use `source` parameter for camelCase conversion
2. **Soft Delete**: Queries automatically filter `del_flag='0'` via BaseViewSet
3. **Pagination**: Optional - only activates when `pageNum` or `pageSize` provided
4. **Bulk Operations**:
   - Delete: Comma-separated IDs in URL (`DELETE /module/1,2,3`)
   - Update: Use `update_body_serializer_class` + `update_body_id_field`
5. **Audit Fields**: Auto-populated (`create_by`, `update_by`) via `@audit_log` decorator
6. **Permissions**: Admin role bypasses all checks, set `required_roles` for other roles
7. **Frontend State**: Use Pinia stores for global state, component `ref()` for local state
8. **API Error Handling**: Unified via response interceptor (401/500/601 codes)
9. **File Upload**: Use `FileUpload` or `ImageUpload` components
10. **SQL Safety**: DataSourceExecutor only allows SELECT queries (no INSERT/UPDATE/DELETE)

### Code Quality Checklist

- [ ] Models inherit from `BaseModel` with `db_table` and `indexes`
- [ ] Serializers inherit from `BaseModelSerializer` with proper `source` mappings
- [ ] ViewSets inherit from `BaseViewSet` with appropriate permissions
- [ ] Frontend components use standard template structure
- [ ] API wrappers use consistent naming (list, get, add, update, delete)
- [ ] Error handling uses unified response format
- [ ] Export functionality uses `ExportExcelMixin`
- [ ] Pagination uses `StandardPagination` (backend) and `<pagination>` component (frontend)
- [ ] Package installations use `uv pip install` (backend) and `pnpm add` (frontend)
