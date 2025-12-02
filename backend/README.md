# 后端（Django + DRF）

## 概述
后端提供系统管理（用户、角色、菜单、字典、参数）、数据源管理、查询执行与查询日志记录能力。接口采用统一响应格式与软删除策略，支持 JWT 认证与 drf-spectacular 文档。

## 目录结构



### backend/config
- settings.py ：REST、JWT、异常、分页等全局配置； AUTH_USER_MODEL='system.User'
- urls.py ：全局路由入口（通常引入各 app 的 urls.py ）

### backend/apps/system
- 职责：系统管理（用户、部门、角色、菜单、字典、配置）
- 路由： urls.py 使用 DefaultRouter 注册资源路由；兼容集合 PUT 的 update_by_body 路由（比如 path('menu', MenuViewSet.as_view({'put': 'update_by_body', 'post':'create'})) ）
- 视图： views/core.py 提供 BaseViewSet （统一响应、分页、集合更新）、登录/验证码/登出、路由树 GetRoutersView 等； views/user.py 、 views/menu.py 、 views/dict.py 等具体资源操作
- 权限： permission.py 提供 HasRolePermission ，视图可声明 required_roles
- 异常： exceptions.py 全局异常包装
- 序列化与分页： serializers.py 定义统一审计字段输出； pagination.py 标准分页结构输出
- 管理命令： management/commands/init_menus.py 初始化系统管理目录与子菜单（用户、部门、角色、菜单、字典、配置）

### backend/apps/datasource
- 职责：数据源管理与查询日志
- 模型： models.py 包含数据源信息（ name , db_type , host , port , database , username , password , params 等）与查询日志（记录 SQL、状态、耗时、错误等）
- 视图： views.py 提供数据源 CRUD、连通性测试、查询接口（ POST /datasource/{id}/query ），渲染 SQL 支持 Django 模板语法（从前端传 {sql, params} ）
- 序列化： serializers.py 输出驼峰命名；列表与详情均遵循统一响应
- 路由： urls.py 注册 REST 路由与扩展动作

### backend/apps/dbutils
- 职责：数据库访问抽象层与执行器
- base.py ：定义统一接口（查询执行、表/库枚举、表结构、字段类型映射、错误处理等）
- factory.py ：根据 db_type 选择具体实现（ sqlite / mysql/mariadb / postgres/postgresql ）
- sqlite.py / mysql.py / postgres.py ：具体驱动实现；支持 list_tables_info 、 get_table_schema 、 execute_query 等

### backend/apps/datameta
- 职责：元数据管理（表与字段）
- 模型： models.py 定义 MetaTable （ data_source 外键、 table_name 、 database 、 comment 等）与 MetaColumn （字段信息与类型、非空、默认值、是否主键等）；遵循审计与软删
- 视图： views.py 提供数据总览、字段查看、采集逻辑（基于数据源连接信息从真实库中抓取表/字段信息）；已按统一响应与分页风格输出
- 序列化与路由： serializers.py 、 urls.py 与系统风格一致

### backend/apps/common/encrypt.py
- 加密工具（通常用于敏感信息处理，如密码加密/解密）



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


