# 后端（Django + DRF）

## 当前定位

后端当前以 **五阶段职责模型** 为基线：

| 模块 | 当前职责 |
|------|----------|
| `datasource` | 数据源管理、连通性测试、数据库/表/字段发现、源数据采集到资产 |
| `dataintegration` | 数据同步任务配置与执行 |
| `datadev` | 脚本开发、模型设计、研发态执行日志 |
| `datatask` | 统一任务、依赖、实例、调度与来源分发 |
| `dataasset` | 资产目录、元数据浏览、表级血缘 |
| `dataservice` | 查询与数据接口服务 |
| `system` | 登录、验证码、JWT、菜单与 RBAC |

当前重要口径：

1. `datasource` 不再维护 snapshot 模型；采集任务定义保留在 `DataSourceCollectionTask`，采集执行实例统一纳入 `datatask.TaskInstance`。
2. `dataintegration` 已改为直接使用 `sourceDatabaseName` / `sourceTableName`。
3. 登录链路当前包含验证码校验与失败次数限流。

## 启动命令

### 开发环境

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py initdata
uv run python manage.py runserver 0.0.0.0:8000
```

### 生产环境部署

后端使用 Django Channels 承载 Web 终端的 WebSocket 通道，生产环境应使用 `daphne` 启动 ASGI 应用，不使用 `gunicorn` 启动。

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run env DJANGO_DEBUG=false DJANGO_SECRET_KEY='<strong-secret>' DATA_ADMIN_ADMIN_PASSWORD='<strong-admin-password>' DATA_ADMIN_USER_PASSWORD='<strong-user-password>' python manage.py initdata
uv run env DJANGO_DEBUG=false DJANGO_SECRET_KEY='<strong-secret>' DJANGO_ALLOWED_HOSTS='example.com,127.0.0.1' daphne -b 127.0.0.1 -p 18001 --access-log /tmp/data-admin-backend-18001-access.log config.asgi:application
```

Nginx 配置见 `../nginx/data-admin.conf`，对外暴露 `/data-admin/`、`/data-api/`、`/api/` 和 `/ws/`，并代理到本机 `18001` 端口。后台托管可使用系统服务管理器，或本地排障时临时使用 `screen`：

```bash
screen -dmS data-admin-daphne-18001 bash -lc 'cd /path/to/data-admin/backend && exec uv run env DJANGO_DEBUG=false DJANGO_SECRET_KEY="<strong-secret>" DJANGO_ALLOWED_HOSTS="example.com,127.0.0.1" daphne -b 127.0.0.1 -p 18001 --access-log /tmp/data-admin-backend-18001-access.log config.asgi:application > /tmp/data-admin-backend-18001-daphne.log 2>&1'
```

- Python：`3.12+`
- 开发 Swagger：`http://localhost:8000/api/docs/`
- 生产 Swagger：`http://localhost:80/api/docs/`

## 常用校验命令

```bash
cd backend
uv run python manage.py check
uv run python manage.py makemigrations --check
uv run python manage.py test apps.datasource apps.dataintegration apps.datadev apps.datatask apps.system
```

## 依赖迁移
```bash
uv export --format requirements-txt --no-hashes -o requirements.txt
```

## 关键目录

```text
backend/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── env.py
└── apps/
    ├── system/
    ├── datasource/
    ├── dataintegration/
    ├── datadev/
    ├── datatask/
    ├── dataasset/
    ├── dataservice/
    ├── dbutils/
    ├── executors/
    ├── monitor/
    └── terminal/
```

## 当前接口前缀

| 前缀 | 模块 |
|------|------|
| `/data-api/` | `system` |
| `/data-api/monitor/` | `monitor` |
| `/data-api/datasource/` | `datasource` |
| `/data-api/dataintegration/` | `dataintegration` |
| `/data-api/datadev/` | `datadev` |
| `/data-api/datatask/` | `datatask` |
| `/data-api/dataasset/` | `dataasset` |
| `/data-api/dataservice/` | `dataservice` |
| `/data-api/terminal/` | `terminal` |

## 统一约定

1. 含 `del_flag` 的模型默认软删除与过滤。
2. API 统一返回 `{ code, msg, data | rows | total }`。
3. 数据源密码加密存储，执行器上下文统一复用 `apps.datasource.executor_info`。
4. 业务模块通过 source handler 与 `source_registry` 接入 `datatask`，平台内核不再反向持有业务分支；其中 `datasource` 当前使用 `task_handler.py`。

## 进一步阅读

- 项目入口：`../README.md`
- 当前状态：`../docs/requirements/active_tasks.md`
- 架构 ADR：`../docs/adr/`
