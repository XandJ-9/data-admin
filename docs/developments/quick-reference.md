# 快速参考

## 项目概览

- **后端**：Django 5.2 + DRF 3.16 + SimpleJWT + Channels 4.3
- **前端**：Vue 3.5 + Element Plus 2.10 + Vite 6 + Pinia 3.0
- **包管理器**：`uv`（后端）、`pnpm`（前端）
- **数据库**：SQLite（开发环境），支持连接外部 MySQL/PostgreSQL/Presto/StarRocks

## 启动命令

### 后端
```bash
cd backend
uv sync                                        # 安装依赖
uv run manage.py migrate                       # 数据库迁移
uv run manage.py initdata                      # 初始化管理员、角色、菜单
uv run manage.py runserver 0.0.0.0:8000        # 启动服务
```

### 前端
```bash
cd frontend
pnpm install                                   # 安装依赖
pnpm dev                                       # 启动开发服务器（端口 80）
```

## 生产环境部署

### 快速部署流程

```bash
# 1. 后端部署
cd backend
uv sync
cat > .env.production << EOF
DEBUG=False
ALLOWED_HOSTS=your.domain.com
SECRET_KEY=<generate-random-key>
DATABASE_ENGINE=django.db.backends.mysql
DATABASE_NAME=dataadmin
DATABASE_USER=dataadmin_user
DATABASE_PASSWORD=<password>
DATABASE_HOST=localhost
DATABASE_PORT=3306
REDIS_URL=redis://localhost:6379/0
EOF

python manage.py migrate
python manage.py init_system
python manage.py collectstatic --noinput

# 启动应用服务器（选择其中一种）
# 推荐：Daphne（支持 WebSocket）
daphne -b 127.0.0.1 -p 8000 config.asgi:application

# 或：Gunicorn（简单同步应用）
# gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 4

# 或：uWSGI（高级功能）
# uwsgi --socket 127.0.0.1:8000 --protocol http --module config.wsgi --callable application

# 2. 前端部署
cd ../frontend
pnpm install --prod
pnpm build:prod
# 输出到 dist/ 目录，由 Nginx 提供静态文件服务
```

### 应用服务器选项

| 服务器 | 协议 | WebSocket | 性能 | 推荐度 | 适用场景 |
|--------|------|----------|------|--------|---------|
| **Daphne** | ASGI | ✅ 完全支持 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **本项目推荐**（Web 终端需要 WebSocket） |
| **Gunicorn** | WSGI | ❌ 不支持 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 纯 HTTP 的同步应用 |
| **uWSGI** | WSGI/ASGI | ⚠️ 需配置 | ⭐⭐⭐⭐ | ⭐⭐ | 需要高级功能的应用 |
| **Hypercorn** | ASGI | ✅ 完全支持 | ⭐⭐⭐⭐⭐ | ⭐⭐ | 高性能异步应用（实验性） |

#### 安装与启动

**Daphne（推荐）**
```bash
pip install daphne
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

**Gunicorn**
```bash
pip install gunicorn
gunicorn config.asgi:application --bind 127.0.0.1:8000 --workers 4
```

**uWSGI**
```bash
pip install uwsgi
uwsgi --socket 127.0.0.1:8000 --protocol http --module config.wsgi --callable application
```

### 部署检查清单

- [ ] 设置 `SECRET_KEY`（强随机密钥）
- [ ] 配置数据库（MySQL 5.7+ 或 PostgreSQL 12+）
- [ ] 配置 Redis（缓存和会话存储）
- [ ] 前端构建并生成 dist/ 产物
- [ ] 配置 Nginx 反向代理（含 WebSocket）
- [ ] 配置 HTTPS 证书（推荐 Let's Encrypt）
- [ ] 配置 Systemd 服务自启
- [ ] 配置日志轮转（logrotate）

### 部署验证

```bash
# 检查后端健康状态
curl http://localhost:8000/data-api/system/health/

# 访问前端
curl http://your.domain.com/
```

📖 **详细部署指南**：见 [README.md](../../README.md#部署) 的生产环境部署章节

## 默认账号

- 用户名：`admin`
- 密码：`admin123`

## API 端点

| 端点 | 地址 |
|------|------|
| 后端 API | `http://localhost:8000/data-api/` |
| Swagger 文档 | `http://localhost:8000/api/docs/` |
| API Schema | `http://localhost:8000/api/schema/` |
| 前端开发 | `http://localhost:80`（代理到后端） |
| WebSocket | `ws://localhost:8000/ws/terminal/` |

## 后端模块

| 模块 | 说明 | 关键模型 |
|------|------|----------|
| `system` | 用户、角色、菜单、部门、岗位、字典、配置 | User, Role, Menu, Dept, DictType, Config |
| `datasource` | 外部数据源连接管理 | DataSource |
| `dataasset` | 元数据采集、表血缘关系 | MetaTable, MetaColumn, MetaCollectionTask, TableLineage |
| `dataservice` | SQL 查询、数据接口服务 | QueryLog, InterfaceInfo, InterfaceField |
| `dataetl` | ETL 任务定义、执行、版本管理 | ETLTask, ETLExecutionLog, ETLTaskVersion |
| `monitor` | 服务器监控、操作日志 | OperLog |
| `terminal` | Web 终端（PTY + WebSocket） | TerminalSession, TerminalCommand |
| `dbutils` | 数据库执行器抽象层 | — |

## 前端模块

| 模块 | 页面路径 | API 路径 |
|------|----------|----------|
| 数据源 | `views/data/datasource/` | `api/data/datasource.js` |
| 元数据 | `views/data/asset/` | `api/data/asset.js`, `api/data/meta.js` |
| ETL | `views/data/etl/` | `api/data/etl.js` |
| 数据服务 | `views/data/service/` | `api/data/service.js` |
| 系统管理 | `views/system/` | `api/system/` |
| 监控 | `views/monitor/` | `api/monitor/` |
| 终端 | `views/terminal/` | `api/terminal.js` |

## 关键文件位置

| 文件 | 说明 |
|------|------|
| `apps/system/models.py` | BaseModel（审计字段、软删除） |
| `apps/system/views/core.py` | BaseViewSet（CRUD 基类） |
| `apps/system/serializers.py` | BaseModelSerializer（camelCase 自动映射） |
| `apps/system/permission.py` | HasRolePermission（角色权限） |
| `apps/system/common.py` | audit_log 审计日志装饰器 |
| `apps/common/mixins.py` | BaseViewMixin（响应辅助方法） |
| `apps/common/pagination.py` | StandardPagination（分页器） |
| `apps/common/exceptions.py` | 全局异常处理器 |
| `apps/common/encrypt.py` | 密码加密工具 |
| `apps/dbutils/factory.py` | get_executor（数据库执行器工厂） |
| `apps/dbutils/base.py` | DataSourceExecutor（执行器基类） |
| `config/settings.py` | Django 配置 |
| `config/urls.py` | 主 URL 路由 |
| `config/routing.py` | WebSocket 路由 |

## 响应格式

```javascript
// 成功 - 列表
{ code: 200, msg: '操作成功', rows: [...], total: 100, pageNum: 1, pageSize: 10 }

// 成功 - 详情
{ code: 200, msg: '操作成功', data: { id: 1, name: '...' } }

// 成功 - 操作
{ code: 200, msg: '操作成功' }

// 错误
{ code: 400|404|500, message: '错误描述' }
```

## URL 注册路径

| URL 前缀 | 模块 |
|----------|------|
| `/data-api/` | system（用户、角色、菜单等） |
| `/data-api/monitor/` | monitor（操作日志、服务器监控） |
| `/data-api/datasource/` | datasource（数据源管理） |
| `/data-api/dataasset/` | dataasset（元数据、血缘） |
| `/data-api/dataetl/` | dataetl（ETL 任务） |
| `/data-api/dataservice/` | dataservice（查询、接口） |
| `/data-api/terminal/` | terminal（终端会话） |
| `/api/docs/` | Swagger 文档 |

## 外部文档

- 后端文档：`backend/README.md`
- 前端文档：`frontend/README.md`
- 开发指南：`docs/architecture/development-guide.md`
- ADR 记录：`docs/adr/`
- 变更日志：`docs/changelog.md`
