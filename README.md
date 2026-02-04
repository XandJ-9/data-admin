# Data Admin

> 一体化数据管理与查询平台，后端基于 Django + DRF，前端基于 Vue3 + Vite，适配 RuoYi-Vue3 风格与权限体系。

## 项目概览

**Data Admin** 是一个统一的数据资产管理平台，提供数据源管理、元数据采集、在线数据查询、表血缘追踪、数据质量管理、任务运维监控等核心功能。

### 核心特性

- **数据源管理** - 支持 MySQL、PostgreSQL、SQLite、Oracle、SQL Server、Presto、StarRocks 等多种数据库
- **元数据管理** - 自动采集数据库、表、字段元数据，支持元数据浏览和搜索
- **表血缘追踪** - 手动配置表级血缘关系，可视化血缘网络，支持影响分析
- **数据查询** - 在线 SQL 查询，支持分页、参数化查询，查询日志审计
- **系统管理** - 用户、角色、菜单、权限管理，登录日志、操作日志
- **监控运维** - 服务监控、任务调度、数据质量检查

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django 5.2 + DRF + JWT |
| 前端 | Vue 3 + Element Plus + Vite + Pinia |
| 数据库 | SQLite / MySQL / PostgreSQL |
| 包管理 | uv (后端) + pnpm (前端) |

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- uv（推荐）或 pip
- pnpm

### 后端启动

```bash
cd backend

# 安装 uv（如果尚未安装）
pip install uv

# 创建虚拟环境
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

### 前端启动

```bash
cd frontend

# 安装 pnpm（如果尚未安装）
npm install -g pnpm

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 访问应用

打开浏览器访问：`http://localhost:5173`

默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`

## 文档

详细文档请查看 [docs/](docs/) 目录：

| 文档 | 说明 |
|------|------|
| [platform-architecture-design.md](docs/platform-architecture-design.md) | 总体架构设计，包含五大模块详细设计 |
| [development-guide.md](docs/development-guide.md) | 开发指南，包含核心抽象层、命名规范、开发模式 |
| [data-asset-module.md](docs/data-asset-module.md) | 数据资产管理模块，包含 API、测试、使用指南 |
| [deployment-guide.md](docs/deployment-guide.md) | 部署指南，包含安装、配置、生产部署 |

### 核心设计

#### 后端抽象层

- **BaseModel** - 所有模型继承，提供审计字段和软删除
- **BaseViewSet** - 统一 CRUD、软删除、审计日志
- **BaseViewMixin** - 统一响应格式
- **DataSourceExecutor** - 数据库执行器抽象，支持多种数据库

#### 前端设计

- **Vue 3 Composition API** - 现代化的组件开发方式
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **动态路由** - 从后端菜单自动生成

## 项目结构

```
data-admin/
├── backend/                 # Django 后端
│   ├── apps/               # 业务应用
│   │   ├── system/         # 系统管理
│   │   ├── dataasset/      # 数据资产管理
│   │   ├── dataservice/    # 数据服务
│   │   └── dbutils/        # 数据库执行器
│   └── config/             # 配置文件
├── frontend/               # Vue3 前端
│   └── src/
│       ├── api/            # API 封装
│       ├── components/     # 通用组件
│       └── views/          # 页面视图
└── docs/                   # 项目文档
```

## 开发规范

- **命名规范**
  - 后端模型/数据库：`snake_case`
  - 后端 Python：`snake_case`
  - API 响应（JSON）：`camelCase`
  - 前端组件：`PascalCase`
  - 前端文件：`kebab-case`

- **REST API**
  - 列表：`GET /module/` with `pageNum`, `pageSize`
  - 详情：`GET /module/{id}/`
  - 创建：`POST /module/`
  - 更新：`PUT /module/{id}/`
  - 删除：`DELETE /module/{id}/`

- **响应格式**
  ```json
  { "code": 200, "msg": "操作成功", "data": {...} }
  { "code": 200, "rows": [...], "total": N, "msg": "操作成功" }
  ```

## 生产部署

### 构建前端

```bash
cd frontend
pnpm build:prod
```

### 复制到后端

```bash
mkdir -p ../backend/dist
cp -r dist/* ../backend/dist/
```

### 启动后端服务

```bash
cd backend
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/backend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /data-api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

详细部署指南请参考：[docs/deployment-guide.md](docs/deployment-guide.md)

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## License

本项目遵循 MIT 许可证。前端适配 RuoYi-Vue3（MIT）。

## 联系方式

- 项目主页：[GitHub Repository]
- 问题反馈：[Issues]
- 文档：[docs/](docs/)

---

**版本**: v1.0.0
**最后更新**: 2025-02-05
