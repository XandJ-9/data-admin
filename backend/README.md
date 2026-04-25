# 后端（Django + DRF）

## 概述

后端基于 Django 5.2 + DRF 3.16 构建，提供系统管理、数据源管理、数据资产管理、数据服务、数据开发与监控运维能力。接口采用统一响应格式与软删除策略，支持 JWT 认证（SimpleJWT）与 drf-spectacular API 文档。

## 运行与开发

```bash
# 创建虚拟环境（推荐 uv）
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

- Python 3.12+
- Swagger 文档：`http://localhost:8000/api/docs/`

## 目录结构

```
backend/
├── config/                        # Django 配置
│   ├── settings.py                #   REST/JWT/分页/异常处理等全局配置
│   ├── urls.py                    #   路由入口（/data-api/ 前缀）
│   └── env.py                     #   数据库连接配置
├── apps/
│   ├── system/                    # 系统管理
│   │   ├── models.py              #   User, Role, Menu, Dept, Post, DictType, DictData, Config, Notice
│   │   ├── views/                 #   BaseViewSet, 登录/登出/验证码, 路由树生成
│   │   ├── permission.py          #   RBAC 权限控制 (HasRolePermission)
│   │   └── management/commands/   #   init_system 初始化命令
│   ├── datasource/                # 数据源管理
│   │   ├── models.py              #   DataSource（连接信息 + 加密密码）
│   │   ├── views.py               #   数据源 CRUD、连通性测试、数据库/表/字段探查接口
│   │   ├── collectors.py          #   源端库表字段探查适配
│   │   └── executor_info.py       #   统一连接上下文构建（解密密码 + 解析参数）
│   ├── dataasset/                 # 数据资产管理
│   │   ├── models.py              #   AssetNamespace, DataAsset, DataAssetColumn, MetaTable, MetaColumn, TableLineage
│   │   ├── services.py            #   规范资产双写与元数据同步
│   │   └── views.py               #   元数据浏览、资产查询、血缘查询
│   ├── dataservice/               # 数据服务
│   │   ├── models.py              #   QueryLog, InterfaceInfo, InterfaceField
│   │   ├── views.py               #   SQL 查询, CSV 导出, 接口执行
│   │   └── custom.py              #   自定义业务逻辑
│   ├── dataintegration/           # 数据集成
│   │   ├── models.py              #   DataIntegrationTask 业务配置模型
│   │   ├── views.py               #   集成任务配置与执行入口
│   │   └── task_source.py         #   向 datatask 注册 DATA_SYNC 来源处理器
│   ├── datadev/                   # 数据开发
│   │   ├── models.py              #   DataDevScript, DataDevModel, DataDevScriptExecution 等
│   │   ├── views.py               #   加工作业、模型设计与执行接口
│   │   └── task_source.py         #   向 datatask 注册 SQL_COMPUTE 来源处理器
│   ├── datatask/                  # 任务运维中心（平台内核）
│   │   ├── models.py              #   Task, TaskDependency, TaskInstance
│   │   ├── services.py            #   统一任务内核服务
│   │   ├── views.py               #   任务、依赖、实例运维接口
│   │   └── source_registry.py     #   任务来源注册与分发协议
│   ├── dbutils/                   # 数据库执行器抽象层
│   │   ├── base.py                #   DataSourceExecutor 接口定义
│   │   ├── factory.py             #   执行器工厂（按 db_type 路由）
│   │   ├── mysql.py               #   MySQL / MariaDB / StarRocks
│   │   ├── postgres.py            #   PostgreSQL
│   │   ├── presto.py              #   Presto / Trino
│   │   └── sqlite.py              #   SQLite
│   ├── monitor/                   # 监控管理
│   │   ├── models.py              #   OperLog, Logininfor
│   │   └── middleware.py          #   操作日志自动记录中间件
│   ├── common/                    # 公共组件
│   │   ├── mixins.py              #   BaseViewMixin（统一响应）
│   │   ├── util_model.py          #   BaseModel（审计字段 + 软删除）
│   │   ├── pagination.py          #   StandardPagination
│   │   ├── exceptions.py          #   统一异常处理
│   │   └── encrypt.py             #   密码加解密
│   └── utils/
│       └── excel.py               #   Excel 导入导出
```

## 推荐分层

| 层级 | 模块 | 角色 |
|------|------|------|
| 业务入口层 | `datasource` | 连接与发现：数据源定义、探查、采集编排 |
| 业务入口层 | `dataintegration` | 数据搬运入仓：贴源同步任务配置与执行 |
| 业务入口层 | `datadev` | 建模与加工：模型定义、脚本开发、研发治理 |
| 平台内核层 | `datatask` | 统一任务、依赖、实例、调度与来源分发 |
| 资产治理层 | `dataasset` | 元数据沉淀、资产语义、兼容模型、血缘基础 |

## 核心抽象层

| 组件 | 位置 | 说明 |
|------|------|------|
| `BaseModel` | `common/util_model.py` | 所有模型继承，提供 `create_by`/`update_by`/`create_time`/`update_time`/`del_flag` 审计字段与软删除 |
| `BaseViewSet` | `system/views/core.py` | 统一 CRUD、软删除、分页、审计日志记录 |
| `BaseViewMixin` | `common/mixins.py` | 统一响应方法：`ok()`, `error()`, `data()`, `csv_response()`, `excel_response()` |
| `BaseModelSerializer` | `system/serializers.py` | 自动 snake_case → camelCase 输出转换 |
| `DataSourceExecutor` | `dbutils/base.py` | 数据库执行器接口（查询/表枚举/结构获取/分页），Factory 模式按 db_type 路由 |
| `HasRolePermission` | `system/permission.py` | RBAC 权限检查，admin 角色自动放行 |
| `@audit_log` | `common/mixins.py` | 操作审计装饰器，自动记录 CRUD 操作 |
| `StandardPagination` | `common/pagination.py` | 标准分页（pageNum/pageSize，默认 10，最大 100） |

## 统一响应格式

所有接口返回统一 JSON 结构，由 `BaseViewSet` 和 `custom_exception_handler` 保证：

```json
// 成功 - 详情
{ "code": 200, "msg": "操作成功", "data": { ... } }

// 成功 - 列表（分页）
{ "code": 200, "msg": "操作成功", "total": 50, "rows": [ ... ] }

// 错误
{ "code": 400, "msg": "错误描述" }
```

## 统一约定

- **软删除**：含 `del_flag` 的模型统一软删（`'0'`=正常, `'1'`=已删除），查询默认过滤 `del_flag='0'`
- **审计字段**：`create_by`/`update_by`/`create_time`/`update_time`，自动填充
- **安全**：敏感信息不返回；密码加密存储（`apps/common/encrypt.py`）
- **认证**：JWT（SimpleJWT），8 小时 Access Token，1 天 Refresh Token
- **权限**：`HasRolePermission` 基于角色检查，admin 角色自动放行

## 开发规范

### 命名规范

| 场景 | 规范 | 示例 |
|------|------|------|
| 模型/数据库字段 | `snake_case` | `create_time`, `data_source` |
| Python 代码 | `snake_case` | `get_queryset()`, `page_size` |
| API 响应 JSON | `camelCase`（由 BaseModelSerializer 自动转换） | `createTime`, `dataSource` |

### REST API 规范

| 操作 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 列表 | GET | `/module/` | 支持 `pageNum`, `pageSize` 分页参数 |
| 详情 | GET | `/module/{id}/` | |
| 创建 | POST | `/module/` | 配合 `@audit_log` 装饰器 |
| 更新 | PUT | `/module/{id}/` | 配合 `@audit_log` 装饰器 |
| 删除 | DELETE | `/module/{id}/` | 软删除，设置 `del_flag='1'` |
| 自定义操作 | 自定义 | `@action(detail=True|False)` | |

### 新模块开发清单

- [ ] Model 继承 `BaseModel`，定义 `Meta.db_table` 和 `indexes`
- [ ] Serializer 继承 `BaseModelSerializer`（自动 camelCase 输出）
- [ ] ViewSet 继承 `BaseViewSet`，create/update 使用 `@audit_log`
- [ ] 分页使用 `paginate_queryset()` + `get_paginated_response()`
- [ ] 路由：`urls.py` 使用 `DefaultRouter(trailing_slash='/?')`
- [ ] 迁移：`python manage.py makemigrations && migrate`
- [ ] 查询使用 ORM 或 dbutils 抽象层，避免裸 SQL
- [ ] 异常使用 DRF 内置异常（ValidationError, NotFound, PermissionDenied）

## API 端点

### 数据源管理 (`/data-api/datasource/`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/datasource/` | 数据源列表 |
| POST | `/datasource/` | 创建数据源 |
| PUT | `/datasource/{id}/` | 更新数据源 |
| DELETE | `/datasource/{id}/` | 删除数据源 |
| POST | `/datasource/test/` | 测试连通性（请求体参数） |
| POST | `/datasource/{id}/test/` | 测试连通性（按 ID） |

### 数据资产管理 (`/data-api/dataasset/`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dataasset/asset-namespace` | 规范资产命名空间列表 |
| GET | `/dataasset/asset` | 规范资产列表 |
| GET | `/dataasset/asset/{id}` | 规范资产详情 |
| GET | `/dataasset/asset-column` | 规范资产字段列表 |
| GET | `/dataasset/asset-column/{id}` | 规范资产字段详情 |
| GET | `/dataasset/meta-table` | 兼容元数据表列表 |
| GET | `/dataasset/meta-table/{id}` | 兼容元数据表详情 |
| POST | `/dataasset/meta-table` | 新增元数据表 |
| PUT | `/dataasset/meta-table/{id}` | 修改元数据表 |
| DELETE | `/dataasset/meta-table/{id}` | 删除元数据表 |
| GET | `/dataasset/meta-column` | 兼容元数据字段列表 |
| GET | `/dataasset/meta-column/{id}` | 兼容元数据字段详情 |
| POST | `/dataasset/meta-column` | 新增元数据字段 |
| PUT | `/dataasset/meta-column/{id}` | 修改元数据字段 |
| DELETE | `/dataasset/meta-column/{id}` | 删除元数据字段 |
| POST | `/datasource/collection/databases` | 获取数据库列表 |
| POST | `/datasource/collection/tables` | 获取表列表 |
| POST | `/datasource/collection/columns` | 获取字段列表 |
| POST | `/datasource/collection/collect` | 同步整库采集 |
| POST | `/datasource/collection/collect-table` | 同步单表采集 |
| POST | `/datasource/collection/collect-async` | 启动异步采集（返回 taskId） |
| GET | `/datasource/collection/collect-status` | 采集进度查询（轮询） |
| POST | `/datasource/collection/collect-cancel` | 取消采集任务 |
| GET | `/dataasset/lineage` | 血缘关系列表 |
| GET | `/dataasset/lineage/upstream` | 上游血缘查询 |
| GET | `/dataasset/lineage/downstream` | 下游血缘查询 |
| GET | `/dataasset/lineage/graph` | 血缘图谱可视化 |

### 数据服务 (`/data-api/dataservice/`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/dataservice/query` | 执行 SQL 查询 |
| POST | `/dataservice/export` | 导出 CSV |
| GET | `/dataservice/query-log/` | 查询日志 |
| GET | `/dataservice/interface-info/` | 接口列表 |
| POST | `/dataservice/interface-info/` | 创建接口 |
| PUT | `/dataservice/interface-info/{id}/` | 更新接口 |
| POST | `/dataservice/interface-info/{id}/execute` | 执行接口 |
| POST | `/dataservice/interface-info/export-meta` | 导出接口定义 (Excel) |
| POST | `/dataservice/interface-info/import-meta` | 导入接口定义 (Excel) |

### 系统管理 (`/data-api/`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/login` | 登录 |
| GET | `/getInfo` | 获取用户信息 |
| GET | `/getRouters` | 获取动态路由（菜单树） |
| - | `/system/user/` | 用户 CRUD |
| - | `/system/role/` | 角色 CRUD |
| - | `/system/menu/` | 菜单 CRUD |
| - | `/system/dept/` | 部门 CRUD |
| - | `/system/post/` | 岗位 CRUD |
| - | `/system/dict-type/` | 字典类型 CRUD |
| - | `/system/dict-data/` | 字典数据 CRUD |
| - | `/system/config/` | 参数配置 CRUD |
| - | `/system/notice/` | 通知公告 CRUD |

### 监控管理 (`/data-api/monitor/`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/monitor/server/` | 服务器状态（CPU/内存/磁盘） |
| GET | `/monitor/online/` | 在线用户 |
| GET | `/monitor/operlog/` | 操作日志 |
| GET | `/monitor/logininfor/` | 登录日志 |

> 完整 API 文档可通过 Swagger UI 查看：`/api/docs/`

## 数据库执行器

通过 Factory 模式按 `db_type` 路由到具体执行器实现：

| 数据库类型 | 执行器类 | db_type 值 |
|-----------|---------|-----------|
| SQLite | `SqliteExecutor` | `sqlite` |
| MySQL / MariaDB / StarRocks | `MysqlExecutor` | `mysql`, `mariadb` |
| PostgreSQL | `PostgresExecutor` | `postgres`, `postgresql` |
| Presto / Trino | `PrestoExecutor` | `presto` |

执行器统一接口：`connect()`, `execute_query()`, `list_tables()`, `get_table_schema()`, `get_table_info()`, `list_tables_info()`, `get_databases()`

查询流程：自动 SELECT 校验 → 方言分页 SQL → 执行 → 格式化结果（datetime/Decimal 转字符串） → 返回 `{columns, rows, next}`
