# Data Admin

> 一体化数据管理平台 — 数据源接入、元数据采集、在线查询、数据接口、数据开发 IDE、Web 终端，开箱即用。

## 简介

Data Admin 是面向数据团队的统一管理平台，覆盖从数据接入到数据消费的全链路。基于 Django + Vue3 构建，前端适配 RuoYi-Vue3 风格，提供完整的 RBAC 权限体系。

## 功能特性

| 模块 | 说明 | 进度 |
|------|------|------|
| **数据源管理** | 多数据库接入（MySQL / PostgreSQL / Presto / Trino / StarRocks 等），连通性测试，连接信息加密存储 | ✅ |
| **元数据管理** | 异步采集数据库/表/字段元信息，增量更新，进度追踪 | ✅ |
| **表血缘追踪** | 配置表级上下游关系，多层递归查询，可视化血缘图谱（当前为轻量级表级血缘） | ✅ |
| **数据查询** | 在线 SQL 编辑执行，参数化查询，结果分页与 CSV 导出 | ✅ |
| **数据接口** | SQL 封装为标准化 API，定义输入/输出字段，支持 Excel 批量管理 | ✅ |
| **数据开发** | Web IDE（三栏布局）、资源导航树、多页签脚本编辑、草稿/发布版本管理、执行记录追踪 | ✅ |
| **Web 终端** | 浏览器内交互式 Shell，多标签页，跨平台 PTY，命令审计 | ✅ |
| **系统管理** | 用户、角色、部门、菜单、字典、参数，完整 RBAC 权限 | ✅ |
| **监控运维** | 已具备服务器状态监控、在线用户与操作日志能力，登录日志与统一菜单入口仍待补齐 | ❌ |

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
python manage.py initdata       # 初始化 admin 用户、角色、菜单
python manage.py sync_menu_data # 将当前数据库菜单同步回 menu_data.json
python manage.py runserver 0.0.0.0:8000
```

### 前端

```bash
cd frontend
pnpm install
pnpm dev
```

> 说明：开发环境默认使用 `80` 端口；在 macOS / Linux 上若当前用户无法绑定特权端口，请使用具备权限的方式启动，或自行调整 Vite 开发端口配置。

### 访问

- 前端：`http://localhost:80/data-admin/`
- API：`http://localhost:8000/data-api/`
- API 文档：`http://localhost:8000/api/docs/`
- 默认账号：`admin` / `admin123`

## 模块重建前检查

当准备按 `ADR-011` 重做一个新模块时，先运行项目内置扫描器检查旧实现：

```bash
python scripts/module_rebuild_guard.py <模块名> --stage <connection|integration|development|orchestration|assetization> --fail-on-hits
```

示例：

```bash
python scripts/module_rebuild_guard.py your_module --stage development --keyword 模块中文名 --keyword 领域关键词
```

脚本默认会扫描 `backend/`、`frontend/src/`、`docs/`、`scripts/`、`deploy/` 以及根目录说明文件，尽量把后端实现、前端入口、菜单/路由、测试、脚本和文档中的旧表达一次性捞出来。

如果确认某些旧路径就是待替换实现，再显式删除：

```bash
python scripts/module_rebuild_guard.py your_module \
  --stage development \
  --delete backend/apps/your_module \
  --delete frontend/src/views/data/your_module \
  --delete frontend/src/api/data/your_module.js \
  --yes
```

> 默认流程：**先扫描、再判边界、后清场、再重建**。

## 项目结构

```
data-admin/
├── backend/              # Django 后端
│   ├── apps/
│   │   ├── system/       # 系统管理（用户/角色/菜单/权限）
│   │   ├── datasource/   # 数据源管理
│   │   ├── dataasset/    # 元数据采集与血缘
│   │   ├── dataservice/  # SQL 查询与数据接口
│   │   ├── datadev/      # 数据开发 IDE（脚本、版本、执行）
│   │   ├── executors/    # 通用执行器能力
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

### 系统要求

- **操作系统**：Linux （推荐 CentOS 7+, Ubuntu 18.04+）
- **Python**：3.12+
- **Node.js**：18+
- **数据库**：SQLite（开发）、MySQL 5.7+ 或 PostgreSQL 12+（生产）
- **内存**：最小 2GB，推荐 4GB+
- **磁盘**：最小 20GB

### 生产环境部署步骤

#### 1. 环境准备

```bash
# 创建应用用户
useradd -m -s /bin/bash dataadmin

# 创建应用目录
mkdir -p /opt/dataadmin && chown dataadmin:dataadmin /opt/dataadmin
cd /opt/dataadmin

# 克隆项目（或上传源码）
git clone https://github.com/yourusername/data-admin.git .
```

#### 2. 后端部署

```bash
# 安装 uv 包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装后端依赖
cd backend
uv sync

# 说明：当前主干尚未接入 .env.production 自动加载。
# 如需生产化配置，请先按实际环境修改 backend/config/settings.py 与 backend/config/env.py。
# 当前默认配置仍以 settings.py 为准（DEBUG=True、ALLOWED_HOSTS=["*"]、SQLite、InMemoryChannelLayer）。

# 数据库初始化（首次部署）
uv run python manage.py migrate
uv run python manage.py initdata        # 创建 admin 用户和初始数据
uv run python manage.py sync_menu_data  # 将当前数据库菜单同步回 menu_data.json

# 收集静态文件
uv run python manage.py collectstatic --noinput

# 启动 Daphne（本项目使用 Django Channels，必须使用 Daphne）
uv run daphne -b 127.0.0.1 -p 8000 config.asgi:application

# 注意：Gunicorn + Uvicorn Worker 无法正确处理 Django Channels 的 WebSocket 路由，不可使用
```

#### 3. 前端部署

```bash
cd ../frontend

# 安装依赖
pnpm install --frozen-lockfile

# 构建生产包
pnpm build:prod

# 验证产物
ls -lh dist/
```

#### 4. 反向代理配置（Nginx）

```nginx
upstream dataadmin_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name your.domain.com;
    
    # 重定向到 HTTPS（生产环境建议启用）
    # return 301 https://$server_name$request_uri;
    
    client_max_body_size 100M;
    
    # 前端静态文件（当前构建基路径为 /data-admin/）
    location /data-admin/ {
        alias /opt/dataadmin/frontend/dist/;
        try_files $uri $uri/ /data-admin/index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # 后端 API
    location /data-api/ {
        proxy_pass http://dataadmin_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 30s;
    }

    # API 文档
    location /api/ {
        proxy_pass http://dataadmin_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket 支持（Web 终端）
    location /ws/ {
        proxy_pass http://dataadmin_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 3600s;
    }
    
    # 日志
    access_log /var/log/nginx/dataadmin_access.log;
    error_log /var/log/nginx/dataadmin_error.log;
}
```

#### 5. Systemd 服务配置

```ini
# /etc/systemd/system/dataadmin.service
[Unit]
Description=Data Admin Backend
After=network.target

[Service]
Type=notify
User=dataadmin
Group=dataadmin
WorkingDirectory=/opt/dataadmin/backend
Environment="PATH=/home/dataadmin/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/dataadmin/.local/bin/uv run daphne -b 127.0.0.1 -p 8000 config.asgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动与管理：

```bash
sudo systemctl daemon-reload
sudo systemctl enable dataadmin
sudo systemctl start dataadmin
sudo systemctl status dataadmin
```

#### 6. 验证部署

```bash
# 检查 API 文档页
curl -I http://localhost:8000/api/docs/

# 检查前端
curl http://your.domain.com/data-admin/

# 访问应用
# 前端：http://your.domain.com/data-admin/
# API 文档：http://your.domain.com/api/docs/
# 默认账号：admin / admin123
```

### 性能调优建议

- **Daphne 并发**：默认单进程异步模式，高并发场景可用 Supervisor/Systemd 启动多实例配合 Nginx 负载均衡
- **数据库连接池**：启用 Redis 缓存可显著提升性能
- **CDN**：生产环境建议为静态资源配置 CDN
- **监控告警**：建议集成 Prometheus/Grafana 监控

### 常见问题

| 问题 | 解决方案 |
|------|---------|
| 502 Bad Gateway | 检查 Daphne 是否启动，查看日志输出 |
| 数据库连接失败 | 验证数据库用户权限，检查 `.env.production` 配置 |
| 前端 404 错误 | 确保 Nginx `root` 指向正确的 `dist` 目录 |
| WebSocket 连接失败 | 确认使用 Daphne（非 Gunicorn），检查 Nginx WebSocket 转发头 |

## 文档

- [开发说明](docs/developments/quick-reference.md)
- [版本日志](docs/changelog.md)
- [架构决策记录](docs/adr/)

## License

MIT
