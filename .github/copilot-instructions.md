# AI Coding Agent Instructions for Data Admin

## Project Overview
**Data Admin** is a unified data management and query platform combining Django + DRF backend with Vue3 + Vite frontend (RuoYi UI style). Core features include data source management, metadata catalog, online query execution, query auditing, and operational monitoring.

### Architecture Layers
- **Backend**: Django 5.x + DRF, abstracted database layer (supports SQLite/MySQL/PostgreSQL/Presto)
- **Frontend**: Vue3 + Element Plus, RuoYi-Vue3 adapted components
- **Data Flow**: UI → API → DRF ViewSet → BaseViewSet (unified response) → Model/Executor → Database

---

## Backend Architecture Patterns

### Core Module Structure (Reference: `backend/apps/system`)
All business modules follow this structure:
```
module/
├── models.py        # Inherit BaseModel for audit fields (create_by/update_by/create_time/update_time/del_flag)
├── serializers.py   # Inherit BaseModelSerializer for camelCase output + audit fields
├── views.py         # ViewSet inherits BaseViewSet for unified response/pagination
├── urls.py          # DRF DefaultRouter with trailing_slash='/?'
└── migrations/      # Auto-generated Django migrations
```

### Data Models: Audit Pattern
All models inherit `BaseModel` (in `system.models`):
```python
class MyModel(BaseModel):
    my_field = models.CharField(...)
    class Meta:
        db_table = 'my_table'
        indexes = [models.Index(fields=['field_name'])]
```
Provides: `create_by`, `update_by`, `create_time`, `update_time`, `del_flag` ('0'=normal, '1'=soft-deleted)

### Response Format: Unified Wrapping
**All endpoints** return structured JSON in `BaseViewSet`:
- Success: `{code: 200, msg: 'message', data: {...}}` (detail) or `{code: 200, msg: '...', rows: [...], total: N}` (list)
- Error: `{code: 400|404|500, message: 'error detail'}` (via `custom_exception_handler`)

Example list response:
```python
def list(self, request, *args, **kwargs):
    queryset = self.get_queryset()
    page = self.paginate_queryset(queryset)
    if page is not None:
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    return self.raw_response({'total': len(queryset), 'rows': serializer.data, 'code': 200})
```

### Database Access: Executor Pattern
Query execution goes through abstracted layer (`dbutils/`):
1. `factory.get_executor(info)` → Returns DB-specific executor (SQLiteExecutor, MySQLExecutor, etc.)
2. `executor.execute_query(sql, params, page_size, offset)` → Returns `{columns: [], rows: [[...]], next?: {...}}`
3. SQL validation: Auto-rejects non-SELECT statements (`_check_sql()`)
4. Pagination: Auto-appended for SELECT queries via `build_pagination_sql()`

**Key files**: `backend/apps/dbutils/base.py` (interface), `factory.py` (routing), `mysql.py`/`postgres.py` (implementations)

### Serialization: Camel Case Convention
- **Output**: Serializers inherit `BaseModelSerializer` which auto-converts snake_case to camelCase
- **Input**: Validate against PaginationQuerySerializer (pageNum, pageSize with defaults)
- Example field mapping: `create_by` → `createBy`, `update_time` → `updateTime`

### Metadata Extraction
When users add new data sources:
1. `DataSource` model stores connection info (host, port, db_name, username, password, params)
2. Call `DataSourceViewSet.@action collect_metadata()` → triggers extraction
3. `_collect_table()` iterates tables, calls `get_table_info()` + `get_table_schema()`
4. Creates/updates `MetaTable` + `MetaColumn` records with audit tracking

---

## Key Data Flows

### Data Source Query Flow
```
Frontend: POST /datasource/{id}/query {sql, params}
  → DataSourceViewSet.query_action()
  → Decrypt password, render SQL with Django template (Template(sql).render(Context(params)))
  → get_executor(info).execute_query(rendered_sql)
  → Log to QueryLog model
  → Return {columns, rows, next}
```

### Metadata Discovery Flow
```
User adds data source → DataSource created
  → Frontend calls collect_metadata endpoint
  → Backend: list_tables_info(info) → returns [{tableName, databaseName, comment, created_time, modified_time}]
  → Create MetaTable for each, extract schema → MetaColumn records
  → Soft-delete old columns when re-collecting
```

---

## Critical Developer Conventions

### REST Endpoint Pattern
- List: `GET /module/` (with pagination params `pageNum`, `pageSize`)
- Detail: `GET /module/{id}`
- Create: `POST /module` with @audit_log decorator
- Update: `PUT /module/{id}` with @audit_log decorator
- Delete: `DELETE /module/{id}` (soft-delete via del_flag)
- Custom action: `@action(detail=False|True, methods=['get'|'post'|...])`

### Error Handling
Always raise DRF exceptions (ValidationError, NotFound, PermissionDenied) - caught by `custom_exception_handler` and wrapped with {code, message}. Unhandled exceptions → 500 response.

### Authentication & Authorization
- JWT via `rest_framework_simplejwt`
- Role-based: `HasRolePermission` checks `request.user.roles` against `required_roles` class attribute
- Admin role (`admin`) bypasses all checks

### Pagination Configuration
- Params: `pageNum` (default 1), `pageSize` (default 10, max 100)
- Response structure: Always include `total` and `rows` keys

---

## Frontend Patterns (Vue3 + RuoYi)

### API Encapsulation
All modules have `src/api/*.js` with consistent endpoint structure:
```javascript
// Example: src/api/datasource.js
export function queryData(query) {
  return request({
    url: '/datasource/query',
    method: 'post',
    data: query
  })
}
```

### View Component Structure
- `src/views/<module>/index.vue` - Main list/search page
- Import API functions, call with search params
- Render table with pagination, sortable columns
- Modals for CRUD forms with validation

### RuoYi Integration Points
- Router auto-generated from backend's `GET /getRouters` → menu tree
- Pagination component: `<pagination v-show="total>0" ... />`
- Dialogs use `<el-dialog>` with form binding
- Table columns typically use `el-table-column` with custom formatters

---

## Important Integration Points

### Database Support Extension
When adding new DB type (e.g., Presto):
1. Add case in `factory.py` → return custom executor instance
2. Create `dbutils/presto.py` implementing `DataSourceExecutor` interface
3. Implement: `connect()`, `execute_query()`, `get_table_schema()`, `list_tables_info()`
4. Handle dialect-specific SQL pagination in `build_pagination_sql()`

### Multi-Tenant Database Scenario
Some data sources have multiple databases per instance (MySQL multiple databases):
- Store `database` field in `MetaTable` to track which DB each table belongs to
- When querying, ensure schema/table selection includes database context
- Filtering in views may need to group by database

### Template SQL Rendering
SQL supports Django template syntax for parameterization:
```sql
SELECT * FROM table WHERE id={{ id }} AND name='{{ name }}'
```
Rendered server-side before execution (security: prevents SQL injection via parameter binding).

---

## Development Checklist

When implementing new features:
- [ ] Model inherits `BaseModel`; define `Meta.db_table` and `indexes`
- [ ] Serializer inherits `BaseModelSerializer` (auto camelCase output)
- [ ] ViewSet inherits `BaseViewSet`; use `@audit_log` for create/update
- [ ] Pagination: use `paginate_queryset()` + return `get_paginated_response()`
- [ ] Add endpoint tests with authentication + pagination
- [ ] Frontend: create API wrapper in `src/api/`, add view component
- [ ] Migration: run `python manage.py makemigrations && migrate` locally
- [ ] No raw SQL: use ORM or abstracted executor layer
- [ ] Soft delete: filter with `del_flag='0'` in querysets

---

## Project Structure Reference
- **Backend entry**: `backend/config/settings.py`, `urls.py`
- **Metadata models**: `backend/apps/datameta/models.py` (MetaTable, MetaColumn)
- **Query executor**: `backend/apps/dbutils/` (base.py, factory.py, driver implementations)
- **System foundation**: `backend/apps/system/models.py` (User, Role, Menu, audit mixins)
- **Frontend UI**: `frontend/src/views/` (organized by module)
- **Configuration docs**: `backend/dev.md` (backend spec), `prd.md` (product roadmap)
