# 后端（Django + DRF）

## 当前定位

后端当前以 **五阶段职责模型** 为基线：

| 模块 | 当前职责 |
|------|----------|
| `datasource` | 数据源管理、连通性测试、数据库/表/字段发现 |
| `dataintegration` | 数据同步任务配置与执行 |
| `datadev` | 脚本开发、模型设计、研发态执行日志 |
| `datatask` | 统一任务、依赖、实例、调度与来源分发 |
| `dataasset` | 资产目录、元数据浏览、表级血缘 |
| `dataservice` | 查询与数据接口服务 |
| `system` | 登录、验证码、JWT、菜单与 RBAC |

当前重要口径：

1. `datasource` 不再维护 snapshot/采集任务模型。
2. `dataintegration` 已改为直接使用 `sourceDatabaseName` / `sourceTableName`。
3. 登录链路当前包含验证码校验与失败次数限流。

## 启动命令

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py initdata
uv run python manage.py runserver 0.0.0.0:8000
```

- Python：`3.12+`
- Swagger：`http://localhost:8000/api/docs/`

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
| `/data-api/terminal/` | `terminal` |

## 统一约定

1. 含 `del_flag` 的模型默认软删除与过滤。
2. API 统一返回 `{ code, msg, data | rows | total }`。
3. 数据源密码加密存储，执行器上下文统一复用 `apps.datasource.executor_info`。
4. 业务模块通过 `task_source.py + source_registry` 接入 `datatask`，平台内核不再反向持有业务分支。

## 进一步阅读

- 项目入口：`../README.md`
- 当前状态：`../docs/requirements/active_tasks.md`
- 架构 ADR：`../docs/adr/`
