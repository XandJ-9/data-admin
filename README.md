# Data Admin

> 一体化数据管理平台 — 数据源接入、元数据采集、在线查询、数据接口、ETL 编排、Web 终端，开箱即用。

## 简介

Data Admin 是面向数据团队的统一管理平台，覆盖从数据接入到数据消费的全链路。基于 Django + Vue3 构建，前端适配 RuoYi-Vue3 风格，提供完整的 RBAC 权限体系。

## 功能特性

| 模块 | 说明 | 进度（是否完成） ｜
|------|------|
| **数据源管理** | 多数据库接入（MySQL / PostgreSQL / Presto / Trino / StarRocks 等），连通性测试，连接信息加密存储 | ✅ ｜
| **元数据管理** | 异步采集数据库/表/字段元信息，增量更新，进度追踪 | ✅ ｜
| **表血缘追踪** | 配置表级上下游关系，多层递归查询，可视化血缘图谱 | ❌ ｜
| **数据查询** | 在线 SQL 编辑执行，参数化查询，结果分页与 CSV 导出 | ✅ ｜
| **数据接口** | SQL 封装为标准化 API，定义输入/输出字段，支持 Excel 批量管理 | ✅ ｜
| **ETL 管理** | DataX / Spark SQL 执行器，全量/增量策略，版本管理，数据质量校验 | ✅ ｜
| **Web 终端** | 浏览器内交互式 Shell，多标签页，跨平台 PTY，命令审计 | ✅ ｜
| **系统管理** | 用户、角色、部门、菜单、字典、参数，完整 RBAC 权限 | ✅ ｜
| **监控运维** | 服务器状态监控，操作日志，登录日志，在线用户管理 | ❌ ｜

## 技术栈

- **后端**：Django 5.2 + DRF 3.16 + SimpleJWT + Channels
- **前端**：Vue 3.5 + Element Plus + Vite 6 + Pinia
- **包管理**：uv（后端）/ pnpm（前端）

## 快速开始

### 后端

```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python manage.py migrate
python manage.py init_system    # 初始化 admin 用户、角色、菜单
python manage.py runserver 0.0.0.0:8000
```

### 前端

```bash
cd frontend
pnpm install
pnpm dev
```

### 访问

- 前端：`http://localhost:80`
- API：`http://localhost:8000/data-api/`
- API 文档：`http://localhost:8000/api/docs/`
- 默认账号：`admin` / `admin123`

## 项目结构

```
data-admin/
├── backend/              # Django 后端
│   ├── apps/
│   │   ├── system/       # 系统管理（用户/角色/菜单/权限）
│   │   ├── datasource/   # 数据源管理
│   │   ├── dataasset/    # 元数据采集与血缘
│   │   ├── dataservice/  # SQL 查询与数据接口
│   │   ├── dataetl/      # ETL 任务编排
│   │   ├── terminal/     # Web 终端
│   │   ├── monitor/      # 监控与审计日志
│   │   └── dbutils/      # 数据库执行器抽象层
│   └── config/           # Django 配置
├── frontend/             # Vue3 前端
│   └── src/
│       ├── api/          # API 封装
│       ├── views/        # 页面组件
│       ├── store/        # Pinia 状态管理
│       └── router/       # 路由（后端动态菜单）
└── docs/                 # 项目文档与 ADR
```

## 部署

```bash
# 构建前端
cd frontend && pnpm build:prod

# 复制到后端静态目录
cp -r dist/* ../backend/dist/

# 启动后端
cd ../backend
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

Nginx 反向代理 `/data-api/` 到后端，静态文件指向 `backend/dist/`。

## 文档

- [开发指南](docs/architecture/development-guide.md)
- [版本日志](docs/changelog.md)
- [架构决策记录](docs/adr/)

## License

MIT
