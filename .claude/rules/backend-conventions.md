# Backend Development Conventions

## Package Management

Use `uv` instead of `pip`:
```bash
uv add <package>
uv pip install <package>
uv pip freeze > requirements.txt
```

## Module Structure

All business modules follow this pattern:
```
module/
├── models.py        # Inherit BaseModel
├── serializers.py   # Inherit BaseModelSerializer
├── views.py         # Inherit BaseViewSet
├── urls.py          # DefaultRouter(trailing_slash='/?')
└── migrations/
```

## Model Pattern

```python
from apps.system.models import BaseModel

class MyModel(BaseModel):
    field_name = models.CharField(max_length=100, verbose_name='Field Name')

    class Meta:
        db_table = 'my_model'
        indexes = [models.Index(fields=['del_flag', 'field_name'])]
```

**BaseModel provides**: `create_by`, `update_by`, `create_time`, `update_time`, `del_flag`

## Serializer Pattern

```python
from apps.system.serializers import BaseModelSerializer

class MySerializer(BaseModelSerializer):
    camelCaseField = serializers.CharField(source='snake_case_field')

    class Meta:
        model = MyModel
        fields = ['id', 'camelCaseField']
```

**Auto-includes**: `createBy`, `updateBy`, `createTime`, `updateTime`, `remark`, `status`

## ViewSet Pattern

```python
from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from apps.system.common import audit_log
from rest_framework.permissions import IsAuthenticated

class MyViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = MyModel.objects.all()
    serializer_class = MySerializer

    @audit_log
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        return self.ok(msg='操作成功')
```

## Naming Conventions

| Context | Convention | Example |
|---------|------------|---------|
| Models/DB fields | `snake_case` | `create_time`, `data_source_id` |
| Python code | `snake_case` | `get_queryset()`, `page_size` |
| API response (JSON) | `camelCase` | `createTime`, `dataSourceId` |

## REST API Patterns

| Operation | Method | Path | Notes |
|-----------|--------|------|-------|
| List | GET | `/module/` | `pageNum`, `pageSize` params |
| Detail | GET | `/module/{id}/` | |
| Create | POST | `/module/` | Use `@audit_log` |
| Update | PUT | `/module/{id}/` | Use `@audit_log` |
| Delete | DELETE | `/module/{id}/` | Soft delete, comma-separated IDs |
| Custom | `@action` | Varies | `detail=True|False` |

## Database Executor Pattern

For external data source queries:

```python
from apps.dbutils.factory import get_executor

info = {'type': 'mysql', 'host': '...', 'port': 3306, ...}
executor = get_executor(info)
result = executor.execute_query(sql, params=None, page_size=10, offset=0)
# Returns: {"columns": [...], "rows": [[...]], "next": {...}|None}
```

Supported types: `sqlite`, `mysql`, `mariadb`, `starrocks`, `postgres`, `postgresql`, `presto`, `trino`

## Key Abstraction Locations

| Component | Location |
|-----------|----------|
| `BaseModel` | `apps/system/models.py` |
| `BaseViewSet` | `apps/system/views/core.py` |
| `BaseViewMixin` | `apps/common/mixins.py` |
| `BaseModelSerializer` | `apps/system/serializers.py` |
| `DataSourceExecutor` | `apps/dbutils/base.py` |
| `HasRolePermission` | `apps/system/permission.py` |
| `StandardPagination` | `apps/common/pagination.py` |

## Common Commands

```bash
cd backend

# Setup
uv venv && .venv\Scripts\activate
uv pip install -r requirements.txt

# Database
uv run manage.py migrate
uv run manage.py makemigrations
uv run manage.py initdata  # admin user, roles, menus

# Run
uv run manage.py runserver 0.0.0.0:8000

# Test
uv run manage.py test apps.<module_name>
```

## Important Notes

1. **Soft Delete**: Queries auto-filter `del_flag='0'` via `BaseViewSet.get_queryset()`
2. **Audit Fields**: Auto-filled by `@audit_log` decorator
3. **Permission**: Set `required_roles = ['role_key']`; admin role bypasses all
4. **SQL Safety**: `DataSourceExecutor._check_sql()` only allows SELECT/WITH/SHOW/DESCRIBE/EXPLAIN
5. **Response Format**: `{code: 200, msg: '...', data: {...}}` or `{code: 200, rows: [...], total: N}`
