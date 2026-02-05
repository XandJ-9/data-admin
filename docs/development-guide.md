# Data Admin 开发指南

本文档面向开发者，提供项目概览、核心抽象层设计、开发规范和快速上手指引。

---

## 项目概览

**Data Admin** 是一个统一数据管理与查询平台，结合 Django + DRF 后端与 Vue3 + Vite 前端（RuoYi-Vue3 UI 风格）。

### 技术栈

- **后端**: Django 5.2 + DRF + SQLite/MySQL/PostgreSQL/Presto 支持
- **前端**: Vue 3 + Element Plus + Vite + Pinia
- **认证**: JWT (django-rest-framework-simplejwt)
- **包管理器**:
  - 后端 Python: **uv** (快速 Python 包安装器)
  - 前端 Node.js: **pnpm** (快速、节省磁盘空间的包管理器)

---

## 常用开发命令

### 后端（Django with uv）

> **重要**: 本项目使用 **uv** 作为 Python 包管理器。始终使用 `uv` 命令而非 `pip`。

```bash
cd backend

# 安装 uv（如果尚未安装）
# pip install uv

# 使用 uv 创建虚拟环境（推荐）
uv venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 使用 uv 安装依赖（比 pip 快得多）
uv pip install -r requirements.txt

# 数据库迁移
python manage.py migrate
python manage.py makemigrations  # 模型更改后创建新迁移

# 运行开发服务器
python manage.py runserver 0.0.0.0:8000

# 初始化系统数据（admin 用户、角色、菜单）
python manage.py init_system

# 测试特定模块
python manage.py test apps.system

# 添加新包 - 使用 uv，而非 pip
uv pip install <package_name>
# 然后更新 requirements.txt:
uv pip freeze > requirements.txt
```

### 前端（Vue3 + Vite with pnpm）

> **重要**: 本项目使用 **pnpm** 作为 Node.js 包管理器。始终使用 `pnpm` 命令而非 `npm` 或 `yarn`。

```bash
cd frontend

# 安装 pnpm（如果尚未安装）
# npm install -g pnpm

# 安装依赖
pnpm install

# 开发服务器
pnpm dev

# 生产构建
pnpm build:prod

# 预发布构建
pnpm build:stage

# 添加新包 - 使用 pnpm，而非 npm 或 yarn
pnpm add <package_name>
pnpm add -D <dev_package_name>
```

### 生产部署

```bash
# 构建前端
cd frontend && pnpm build:prod

# 复制构建产物到后端（backend/dist/ 提供静态文件服务）
cp -r ./dist/* ../backend/dist/

# 使用 gunicorn (WSGI) 或 uvicorn (ASGI) 运行后端
cd backend
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

---

## 架构与代码组织

### 后端结构

```
backend/
├── config/          # Django 设置、urls、wsgi/asgi
├── apps/
│   ├── system/      # 用户、角色、菜单、部门、字典、配置、公告、岗位
│   ├── dataasset/   # 数据资产管理（数据源、元数据、血缘）
│   ├── dataservice/ # 查询执行、查询日志、接口信息
│   ├── dataintegration/ # 集成任务
│   ├── datastudio/  # 数据工作室
│   ├── datataskmonitor/ # 定时任务
│   ├── monitor/     # 服务器监控、登录日志
│   ├── dbutils/     # 数据库执行器抽象层
│   ├── common/      # 基础混入类、分页、加密
│   └── utils/       # Excel 导出工具
└── manage.py
```

### 核心抽象

#### BaseModel

所有模型继承自 `BaseModel` 以获得审计字段：`create_by`、`update_by`、`create_time`、`update_time`、`del_flag`

软删除模式：`del_flag='0'`（正常）、`'1'`（已删除）

模型模式：
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

**位置**: [backend/apps/system/models.py:5](../backend/apps/system/models.py)

#### BaseViewSet

继承自 `BaseViewMixin` + `viewsets.ModelViewSet`
- 在 `get_queryset()` 中自动过滤 `del_flag='0'`
- 使用 `@audit_log` 装饰器进行创建/更新/删除操作
- 支持批量删除（URL 中的逗号分隔 ID）
- 标准 CRUD 响应格式

**位置**: [backend/apps/system/views/core.py:21](../backend/apps/system/views/core.py)

#### BaseViewMixin

提供统一的响应方法：
- `ok(msg='操作成功')` - 成功响应
- `error(msg='操作失败')` - 错误响应
- `data(data, msg='操作成功')` - 数据响应
- `not_found(msg='未找到')` - 404 响应
- `csv_response(columns, rows, filename, bom=False)` - CSV 导出
- `excel_response(filename, workbook)` - Excel 导出

**位置**: [backend/apps/common/mixins.py:6](../backend/apps/common/mixins.py)

#### BaseModelSerializer

自动将 snake_case 转换为 API 响应的 camelCase
自动包含常用审计字段：`createBy`、`updateBy`、`createTime`、`updateTime`、`remark`、`status`

字段命名：使用 `source` 参数将模型字段映射到 camelCase

```python
class MySerializer(BaseModelSerializer):
    customField = serializers.CharField(source='custom_field')

    class Meta:
        model = MyModel
        fields = ['id', 'customField', 'status', 'createTime']
```

**位置**: [backend/apps/system/serializers.py:17](../backend/apps/system/serializers.py)

#### StandardPagination

分页类，使用 `pageNum`/`pageSize` 查询参数
分页是可选的：仅在提供 `pageNum` 或 `pageSize` 时应用
响应格式：`{code: 200, total: N, pageNum: X, pageSize: Y, rows: [...], msg: '操作成功'}`
最大页面大小：100 条记录

**位置**: [backend/apps/common/pagination.py:5](../backend/apps/common/pagination.py)

#### HasRolePermission

基于角色的访问控制
在 ViewSet 上设置 `required_roles = ['role_key']`
Admin 角色（`admin`）绕过所有权限检查

**位置**: [backend/apps/system/permission.py:5](../backend/apps/system/permission.py)

#### DataSourceExecutor

数据库操作的抽象基类，适用于 SQLite/MySQL/PostgreSQL/Presto

关键方法：
- `execute_query(sql, params=None, page_size=10, offset=0)` - 安全的 SQL 执行，带分页
- `list_tables()` - 列出所有表
- `get_table_schema(table_name)` - 获取列信息
- `get_table_info(table_name)` - 获取表元数据
- `list_tables_info()` - 列出所有表的元数据

SQL 安全性：`_check_sql()` 仅允许 SELECT/WITH/SHOW/DESCRIBE/EXPLAIN
通过 `build_pagination_sql()` 自动分页

**位置**: [backend/apps/dbutils/base.py:5](../backend/apps/dbutils/base.py)

### 前端结构

```
frontend/src/
├── api/             # 每个模块的 API 封装（datasource.js、datameta.js 等）
├── components/      # 可复用组件
│   ├── Pagination/  # 标准分页组件
│   ├── Editor/      # 代码编辑器（Monaco）
│   ├── FileUpload/  # 文件上传组件
│   └── ...
├── views/           # 按模块组织的页面组件
├── router/          # Vue Router 配置（从后端自动生成）
├── store/           # Pinia 状态模块（user、permission、dict、settings）
├── utils/           # 请求拦截器、认证、字典工具
└── main.js          # 应用入口点
```

#### 关键前端组件

**Pagination** ([components/Pagination](../frontend/src/components/Pagination/index.vue))
- Props: `total`、`page`、`limit`、`pageSizes`、`layout`
- Emits: `pagination` 事件，包含 `{page, limit}`
- 页面更改时自动滚动到顶部

**API Request** ([utils/request.js](../frontend/src/utils/request.js:1))
- 基于 Axios，带拦截器
- 通过 `Authorization: Bearer <token>` 自动注入 JWT token
- 处理 401（重定向到登录）、500（错误消息）、601（警告）
- 防止重复提交（1 秒间隔）
- 下载方法：`download(url, params, filename, config)`

**Pinia Store** ([store/modules/user.js](../frontend/src/store/modules/user.js:8))
- `useUserStore`: 管理用户状态（token、角色、权限）
- Actions: `login()`、`getInfo()`、`logOut()`
- 使用 base API 路径自动更新头像 URL
- 默认角色：如果未分配角色，则为 `ROLE_DEFAULT`

---

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 后端模型/数据库 | snake_case | `user_name`、`create_time` |
| 后端 Python | 函数/变量使用 snake_case | `get_user_list()` |
| API 响应（JSON） | camelCase | `userName`、`createTime` |
| 前端组件 | PascalCase | `UserList`、`DataSourceForm` |
| 前端文件 | kebab-case | `user-list.vue`、`api-datasource.js` |
| 前端 Props/Methods | camelCase | `handleQuery`、`dataList` |

---

## REST API 模式

- 列表：带 `pageNum`、`pageSize` 查询参数的 `GET /module/`
- 详情：`GET /module/{id}/`
- 创建：带请求体的 `POST /module/`
- 更新：`PUT /module/{id}/`（也支持通过带请求体的 PUT `/module/` 进行批量更新）
- 删除：`DELETE /module/{id}/`（通过 `del_flag` 软删除，支持逗号分隔的 ID）
- 自定义操作：`@action(detail=True\|False, methods=['post'], url_path='path')`

所有端点返回结构化 JSON：
- 成功：`{code: 200, msg: 'message', data: {...}}` 或 `{code: 200, rows: [...], total: N, msg: '...'}`
- 错误：`{code: 400\|404\|500, msg: 'error message'}`

---

## 序列化：驼峰命名输出

序列化器继承 `BaseModelSerializer`，自动将 snake_case 转换为 camelCase
示例：`create_by` → `createBy`、`update_time` → `updateTime`
来自前端的输入参数使用 camelCase（例如：`dataSourceId`、`pageNum`）

---

## 认证与授权

- 通过 `django-rest-framework-simplejwt` 实现 JWT
- 权限类：`[IsAuthenticated, HasRolePermission]`
- 基于角色：在 ViewSet 上设置 `required_roles = ['role_key']`
- Admin 角色（`admin`）绕过所有检查

---

## 数据库查询

对于数据源查询，使用执行器抽象：

```python
from apps.dbutils.factory import get_executor

info = {'type': 'mysql', 'host': '...', 'port': 3306, ...}
executor = get_executor(info)
result = executor.execute_query(sql, params=None, page_size=10, offset=0)
# 返回：{"columns": [...], "rows": [[...]], "next": {...}|None}
```

---

## 元数据采集模式

从数据源采集元数据时：
1. 使用 `list_tables_info()` 获取表元数据
2. 对每个表调用 `get_table_schema()` 获取列信息
3. 创建/更新 `MetaTable` 和 `MetaColumn` 记录
4. 重新导入前软删除旧列（`del_flag='1'`）
5. 字段 `order`（从 1 开始）在 `get_table_schema()` 中返回，用于稳定的列排序

---

## 添加新功能

### 创建新模块

1. 在 `apps/` 下创建 Django 应用目录
2. 定义继承自 `BaseModel` 的模型
3. 创建继承自 `BaseModelSerializer` 的序列化器
4. 创建继承自 `BaseViewSet` 的 ViewSet
5. 在模块 `urls.py` 中注册 URL，并在 `config/urls.py` 中引入
6. 运行 `python manage.py makemigrations && python manage.py migrate`
7. 在 `src/api/{module}.js` 中创建前端 API 封装
8. 在 `src/views/{module}/` 中创建视图组件

**包安装**：
- 后端 Python 包：使用 `uv pip install <package>`（而非 `pip install`）
- 前端 Node.js 包：使用 `pnpm add <package>`（而非 `npm install` 或 `yarn add`）

---

## 前端视图组件模式

- 从 `src/api/{module}.js` 导入 API 函数
- 列表视图使用 `<pagination>` 组件
- 创建/编辑表单使用 `<el-dialog>`
- 数据显示使用 `el-table`，`:data="dataList"`
- 导出方法：`getList()`、`handleQuery()`、`resetQuery()`、`handleAdd()`、`handleUpdate()`、`handleDelete()`

---

## 常见陷阱

1. **序列化器字段映射**：始终为驼峰命名转换使用 `source` 参数
2. **软删除**：查询通过 BaseViewSet 自动过滤 `del_flag='0'`
3. **分页**：可选 - 仅在提供 `pageNum` 或 `pageSize` 时激活
4. **批量操作**：
   - 删除：URL 中的逗号分隔 ID（`DELETE /module/1,2,3`）
   - 更新：使用 `update_body_serializer_class` + `update_body_id_field`
5. **审计字段**：通过 `@audit_log` 装饰器自动填充（`create_by`、`update_by`）
6. **权限**：Admin 角色绕过所有检查，为其他角色设置 `required_roles`
7. **前端状态**：全局状态使用 Pinia stores，组件本地状态使用组件 `ref()`
8. **API 错误处理**：通过响应拦截器统一处理（401/500/601 代码）
9. **文件上传**：使用 `FileUpload` 或 `ImageUpload` 组件
10. **SQL 安全**：DataSourceExecutor 仅允许 SELECT 查询（无 INSERT/UPDATE/DELETE）

---

## 代码质量清单

- [ ] 模型继承自 `BaseModel`，包含 `db_table` 和 `indexes`
- [ ] 序列化器继承自 `BaseModelSerializer`，带有正确的 `source` 映射
- [ ] ViewSet 继承自 `BaseViewSet`，带有适当的权限
- [ ] 前端组件使用标准模板结构
- [ ] API 封装使用一致的命名（list、get、add、update、delete）
- [ ] 错误处理使用统一的响应格式
- [ ] 导出功能使用 `ExportExcelMixin`
- [ ] 分页使用 `StandardPagination`（后端）和 `<pagination>` 组件（前端）
- [ ] 包安装使用 `uv pip install`（后端）和 `pnpm add`（前端）
