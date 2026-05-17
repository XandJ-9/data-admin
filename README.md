# Data Admin

> 统一数据管理平台：覆盖连接与发现、数据集成、数据开发、任务运维、资产与服务五个阶段。

## 当前项目状态

当前主干以 **ADR-010 + ADR-011** 为架构基线，模块职责已收敛为：

| 阶段 | 模块 | 当前职责 |
|------|------|----------|
| Connection & Discovery | `datasource` | 数据源管理、连通性测试、数据库/表/字段发现、源数据采集到资产 |
| Data Integration | `dataintegration` | 贴源同步任务配置与执行 |
| Data Development | `datadev` | 脚本开发、模型设计、研发态执行记录 |
| Orchestration & DataOps | `datatask` | 统一任务、依赖、实例、调度与来源分发 |
| Assetization & Service | `dataasset` / `dataservice` | 资产目录、血缘、查询与接口服务 |

当前重要口径：

1. `datasource` 已不再维护 snapshot 模型；当前通过 `DataSourceCollectionTask + task_handler` 保留单表采集与整库异步采集能力，采集执行记录统一进入 `datatask.TaskInstance`。
2. `dataintegration` 已改为直接填写 `sourceDatabaseName` / `sourceTableName`，不再依赖 snapshot 选择。
3. 删除数据源不会再被历史集成任务阻塞；若任务失去数据源绑定，需重新绑定后再执行。
4. 登录链路当前包含验证码校验与失败次数限流。

## 技术栈

- **后端**：Django 5.2 + DRF 3.16 + SimpleJWT + Channels
- **前端**：Vue 3.5 + Element Plus 2.10 + Vite 6 + Pinia
- **包管理器**：`uv`（后端）、`pnpm`（前端）
- **开发数据库**：SQLite

## 快速开始

### 后端

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py initdata
uv run python manage.py runserver 0.0.0.0:8000
```

### 前端

```bash
cd frontend
pnpm install
pnpm dev
```

### 访问地址

- 前端：`http://localhost:80/data-admin/`
- API：`http://localhost:8000/data-api/`
- API 文档：`http://localhost:8000/api/docs/`
- 默认账号：`admin / admin123`

## 开发约束

1. 新模块或重构模块前，先看 `docs/adr/ADR-011-平台五阶段职责划分规范.md`
2. 提交前同步更新 `docs/requirements/active_tasks.md` 与 `docs/changelog.md`
3. 默认遵循：**主干稳定、短分支交付、单分支单目标**

## 文档入口

- 统一入口：`docs/README.md`
- 当前状态：`docs/requirements/active_tasks.md`
- 架构决策：`docs/adr/`
- 历史归档：`docs/archive/`

## 目录结构

```text
data-admin/
├── backend/                      # Django 后端
│   ├── apps/
│   │   ├── datasource/          # 连接与发现
│   │   ├── dataintegration/     # 数据集成
│   │   ├── datadev/             # 数据开发
│   │   ├── datatask/            # 任务运维内核
│   │   ├── dataasset/           # 资产与血缘
│   │   ├── dataservice/         # 查询与接口服务
│   │   ├── system/              # 用户/角色/菜单/登录
│   │   └── terminal/            # Web 终端
│   └── config/
├── frontend/
│   └── src/
│       ├── api/
│       ├── views/
│       ├── store/
│       └── router/
└── docs/
```
