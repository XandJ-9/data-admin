# 快速参考

## 当前环境

- 后端：Django 5.2 + DRF 3.16 + Channels
- 前端：Vue 3.5 + Element Plus 2.10 + Vite 6
- 包管理器：`uv` / `pnpm`
- 开发数据库：SQLite

## 启动命令

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

## 常用验证命令

```bash
cd backend
uv run python manage.py check
uv run python manage.py makemigrations --check
uv run python manage.py test apps.datasource apps.dataasset apps.dataintegration apps.datadev apps.datatask apps.system

cd ../frontend
pnpm build:prod
```

## 当前访问地址

- 前端：`http://localhost:80/data-admin/`
- API：`http://localhost:8000/data-api/`
- Swagger：`http://localhost:8000/api/docs/`
- 默认账号：`admin / admin123`

## Git 分支命名

```bash
feat/<topic>
fix/<topic>
refactor/<module>
docs/<topic>
hotfix/<topic>
```

## 当前模块入口

| 层级 | 后端模块 | 前端页面 |
|------|----------|----------|
| 连接与发现 | `apps.datasource` | `views/data/datasource/` |
| 数据集成 | `apps.dataintegration` | `views/data/integration/` |
| 数据开发 | `apps.datadev` | `views/data/dev/` |
| 任务运维 | `apps.datatask` | `views/data/task/`, `views/data/orchestration/` |
| 资产与服务 | `apps.dataasset`, `apps.dataservice` | `views/data/asset/`, `views/data/service/` |

## 当前文档入口

1. `docs/README.md`
2. `docs/requirements/active_tasks.md`
3. `docs/changelog.md`
4. `docs/adr/ADR-011-平台五阶段职责划分规范.md`
