# 后端开发规范

## 技术栈

- **框架**：Django 5.2 + DRF 3.16 + SimpleJWT + drf-spectacular
- **WebSocket**：Django Channels 4.3 + Daphne（ASGI 服务器）
- **数据库**：PostgreSQL（默认，读取 `backend/config/env.py`，可通过 `DJANGO_DATABASE_*` 环境变量覆盖为 SQLite 或其他后端），支持连接外部 MySQL/PostgreSQL/Presto/StarRocks
- **包管理器**：`uv`

## 包管理

使用 `uv` 代替 `pip`：
```bash
uv add <package>          # 添加依赖到 pyproject.toml
uv sync                   # 根据 pyproject.toml 同步依赖
uv pip install <package>  # 直接安装（不推荐）

uv export --format requirements-txt --no-hashes -o requirements.txt  # 生成 requirements.txt

```

## 模块目录结构

### 简单模块（单文件）
```
module/
├── models.py        # 继承 BaseModel
├── serializers.py   # 继承 BaseModelSerializer
├── views.py         # 继承 BaseViewSet
├── urls.py          # DefaultRouter(trailing_slash='/?')
└── migrations/
```

### 复杂模块（分层目录，如 datadev）
```
module/
├── models.py
├── urls.py
├── views/           # 按功能拆分视图
│   ├── __init__.py
│   └── task.py
├── serializers/     # 按功能拆分序列化器
│   ├── __init__.py
│   └── task.py
├── services/        # 业务逻辑层
│   ├── __init__.py
│   └── task_service.py
└── migrations/
```

> 任务级执行器统一放在 `apps.executors`，数据库级查询与探查统一放在 `apps.dbutils`。业务模块目录下默认不再新增本地 `executors/`，除非只是非常薄的适配层且已在文档中说明收敛方向。

## Model 模式

```python
from django.db import models
from apps.system.models import BaseModel

class MyModel(BaseModel):
    name = models.CharField(max_length=100, verbose_name='名称')
    status = models.CharField(max_length=1, choices=[('0', '正常'), ('1', '停用')], default='0')

    class Meta:
        db_table = 'my_model'
        indexes = [models.Index(fields=['del_flag', 'name'])]
```

**BaseModel 提供的字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `create_by` | CharField(64) | 创建者用户名 |
| `update_by` | CharField(64) | 更新者用户名 |
| `create_time` | DateTimeField | 创建时间（auto_now_add） |
| `update_time` | DateTimeField | 更新时间（auto_now） |
| `del_flag` | CharField(1) | 软删除标记：`'0'`=正常, `'1'`=已删除 |

## Serializer 模式

```python
from apps.system.serializers import BaseModelSerializer

class MySerializer(BaseModelSerializer):
    # snake_case → camelCase 字段映射
    camelCaseField = serializers.CharField(source='snake_case_field')

    class Meta:
        model = MyModel
        fields = ['id', 'name', 'camelCaseField']
```

**自动包含的 camelCase 字段**（通过 `__init_subclass__()` 自动合并到子类 `Meta.fields`）：

| 序列化字段 | 对应模型字段 | 属性 |
|-----------|------------|------|
| `createBy` | `create_by` | 只读 |
| `updateBy` | `update_by` | 只读 |
| `createTime` | `create_time` | 只读，格式：`%Y-%m-%d %H:%M:%S` |
| `updateTime` | `update_time` | 只读，格式：`%Y-%m-%d %H:%M:%S` |
| `remark` | `remark` | 可选，允许空值 |
| `status` | `status` | 可选 |

## ViewSet 模式

```python
from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from apps.system.common import audit_log
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

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

### BaseViewSet 内置行为

| 方法 | 说明 |
|------|------|
| `get_queryset()` | 自动过滤 `del_flag='0'` |
| `list()` | 分页返回 `{code, rows, total}` |
| `create()` | 自动填充 `create_by`, `update_by`，带 `@audit_log` |
| `retrieve()` | 返回 `{code, msg, data}` |
| `update()` | 自动填充 `update_by`，带 `@audit_log` |
| `partial_update()` | 部分更新（PATCH），带 `@audit_log` |
| `destroy()` | 软删除（`del_flag='1'`），支持逗号分隔 ID 批量删除 |
| `get_object()` | 支持逗号分隔 ID：`/resource/1,2,3/` |

### 可自定义属性

```python
class MyViewSet(BaseViewSet):
    required_roles = ['admin', 'editor']         # 角色权限列表
    create_serializer_class = MyCreateSerializer  # 创建专用序列化器
    update_serializer_class = MyUpdateSerializer  # 更新专用序列化器
    retrieve_serializer_class = MyDetailSerializer  # 详情专用序列化器
    update_body_id_field = 'id'                   # body 中的主键字段名
```

### 响应辅助方法（BaseViewMixin）

```python
self.ok(msg='操作成功')                           # → {code: 200, msg}
self.error(msg='操作失败')                        # → {code: 400, msg}
self.data(data, msg='操作成功')                   # → {code: 200, msg, data}
self.not_found(msg='未找到')                      # → {code: 404, msg}
self.csv_response(columns, rows, filename)        # → CSV 文件下载
self.excel_response(filename, workbook)           # → Excel 文件下载
```

## 分页配置

使用 `StandardPagination`（全局默认分页器）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `pageNum` | 1 | 页码（前端传入） |
| `pageSize` | 10 | 每页条数，最大 100 |

**返回格式**：
```json
{
  "code": 200,
  "msg": "操作成功",
  "total": 100,
  "pageNum": 1,
  "pageSize": 10,
  "rows": [...]
}
```

## 命名规范

| 场景 | 命名风格 | 示例 |
|------|----------|------|
| 模型/数据库字段 | `snake_case` | `create_time`, `data_source_id` |
| Python 代码 | `snake_case` | `get_queryset()`, `page_size` |
| API 响应（JSON） | `camelCase` | `createTime`, `dataSourceId` |
| URL 路径 | `kebab-case` 或全小写 | `/data-api/datasource/` |

## REST API 模式

| 操作 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 列表 | GET | `/module/` | 支持 `pageNum`, `pageSize` 分页参数 |
| 详情 | GET | `/module/{id}/` | |
| 创建 | POST | `/module/` | 使用 `@audit_log` 装饰器 |
| 更新 | PUT | `/module/{id}/` | 使用 `@audit_log` 装饰器 |
| 部分更新 | PATCH | `/module/{id}/` | 使用 `@audit_log` 装饰器 |
| 删除 | DELETE | `/module/{id}/` | 软删除，支持逗号分隔 ID 批量删除 |
| 自定义动作 | `@action` | 自定义 | `detail=True\|False` |

## 权限控制

```python
from apps.system.permission import HasRolePermission

class MyViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    required_roles = ['role_key1', 'role_key2']  # 可选，不设置则仅需登录
```

- `HasRolePermission` 检查用户是否拥有 `required_roles` 中的任一角色
- `admin` 角色自动绕过所有权限检查
- 未设置 `required_roles` 时，仅要求 `IsAuthenticated`

## 异常处理

全局异常处理器 `apps/common/exceptions.py`：
- 所有 DRF 和 Django 异常统一捕获
- 返回格式：`{code: HTTP_STATUS, message: '错误描述'}`
- 处理 `ProtectedError`、`RestrictedError`、`DatabaseError` 等

## 数据库执行器

用于外部数据源查询：

```python
from apps.dbutils.factory import get_executor

info = {'type': 'mysql', 'host': '...', 'port': 3306, 'db_name': '...', 'username': '...', 'password': '...'}
executor = get_executor(info)
```

**支持的数据库类型**：`sqlite`, `mysql`, `mariadb`, `starrocks`, `postgres`, `postgresql`, `presto`, `trino`

**执行器方法**：

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `test_connection()` | Boolean | 测试连接，失败抛出异常 |
| `execute_query(sql, params, page_size, offset)` | `{columns, rows, next}` | 执行 SQL 查询（仅允许 SELECT） |
| `list_tables()` | `[table_name, ...]` | 获取表名列表 |
| `get_table_schema(table)` | `[{order, name, type, ...}, ...]` | 获取表结构 |
| `list_tables_info()` | `[{tableName, comment, ...}, ...]` | 获取表详情列表 |
| `get_table_info(table)` | `dict` | 获取单表详细信息 |
| `get_databases()` | `[db_name, ...]` 或 `None` | 获取数据库列表 |

**SQL 安全**：`_check_sql()` 仅允许 `SELECT`、`WITH`、`SHOW`、`DESCRIBE`、`EXPLAIN` 前缀的语句。

## 业务模块与统一执行层约束

后续涉及 `datasource`、`dataintegration`、`datadev` 的开发，必须同时遵守 `docs/developments/module-responsibility-execution-guide.md`：

1. `datasource`、`dataintegration`、`datadev` 负责业务定义、单次调试执行入口和发布任务到任务中心。
2. `datatask` 负责平台任务镜像、调度索引、依赖和唯一执行实例中心。
3. 外部数据库连接、SQL 查询、库表字段探查必须通过 `apps.dbutils`。
4. DataX、Spark/Hive、MVP/Mock、建模执行等任务级执行必须通过 `apps.executors`。
5. 业务模块不得直接引入外部数据库驱动并自行连接外部数据源。
6. 业务模块不得新增私有执行历史表，所有执行历史必须进入 `datatask.TaskInstance`。
7. 新来源模块接入任务中心必须注册 `apps.datatask.source_registry.SourceHandler`。

## 关键抽象位置

| 组件 | 文件位置 |
|------|----------|
| `BaseModel` | `apps/system/models.py` |
| `BaseViewSet` | `apps/system/views/core.py` |
| `BaseViewMixin` | `apps/common/mixins.py` |
| `BaseModelSerializer` | `apps/system/serializers.py` |
| `DataSourceExecutor` | `apps/dbutils/base.py` |
| `get_executor` | `apps/dbutils/factory.py` |
| `ExecutorFactory` | `apps/executors/base.py` |
| `HasRolePermission` | `apps/system/permission.py` |
| `StandardPagination` | `apps/common/pagination.py` |
| `custom_exception_handler` | `apps/common/exceptions.py` |
| `audit_log` | `apps/system/common.py` |

## 常用命令

```bash
cd backend

# 环境搭建
uv venv && .venv\Scripts\activate
uv sync                           # 根据 pyproject.toml 安装依赖

# 数据库迁移
uv run manage.py makemigrations
uv run manage.py migrate
uv run manage.py initdata         # 初始化管理员用户、角色、菜单

# 启动服务
uv run manage.py runserver 0.0.0.0:8000

# 测试
uv run manage.py test apps.<module_name>
```

## 重要注意事项

1. **软删除**：`BaseViewSet.get_queryset()` 自动过滤 `del_flag='0'` 的记录
2. **审计字段**：`create_by`、`update_by` 由 `@audit_log` 装饰器和 `perform_create/perform_update` 自动填充
3. **角色权限**：设置 `required_roles = ['role_key']`；`admin` 角色自动绕过所有检查
4. **SQL 安全**：`DataSourceExecutor._check_sql()` 仅允许查询类 SQL，禁止增删改和 DDL
5. **响应格式**：成功 `{code: 200, msg, data}` 或 `{code: 200, rows, total}`；错误 `{code: 400|404|500, message}`
6. **JWT 认证**：Access Token 有效期 8 小时，Refresh Token 有效期 1 天
7. **WebSocket**：通过 Django Channels + Daphne 提供 WebSocket 支持（如 Terminal 模块）
8. **密码加密**：数据源密码使用 `apps/common/encrypt.py` 提供的加密存储
