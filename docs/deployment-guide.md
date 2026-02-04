# 部署指南

本文档提供 Data Admin 平台的安装、配置和部署指南。

---

## 环境要求

### 后端

- Python 3.12+
- Django 5.2
- 数据库：SQLite（默认）、MySQL 或 PostgreSQL

### 前端

- Node.js 18+
- pnpm 8+

---

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd data-admin
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境（推荐使用 uv）
pip install uv
uv venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt

# 运行迁移
python manage.py migrate

# 初始化系统数据（admin 用户、角色、菜单）
python manage.py init_system

# 启动开发服务器
python manage.py runserver 0.0.0.0:8000
```

### 3. 前端设置

```bash
cd frontend

# 安装 pnpm（如果尚未安装）
npm install -g pnpm

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 4. 访问应用

打开浏览器访问：`http://localhost:5173`

默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`

---

## 数据资产管理模块配置

### 添加菜单

使用 Django 命令自动添加数据资产管理菜单：

```bash
cd backend
source .venv/bin/activate
python manage.py add_dataasset_menu
```

**执行后自动创建：**
- ✅ 一级菜单：数据资产管理
- ✅ 二级菜单：数据资产概览
- ✅ 二级菜单：数据源管理
- ✅ 二级菜单：元数据浏览
- ✅ 二级菜单：表血缘管理

**强制更新所有菜单配置：**
```bash
python manage.py add_dataasset_menu --force
```

### 手动执行 SQL（备选方案）

如果命令失败，可以手动执行 SQL：

```sql
-- 创建一级菜单
INSERT INTO sys_menu (
    menu_name, parent_id, order_num, path, component,
    route_name, is_frame, is_cache, menu_type, visible,
    status, perms, icon, create_by, create_time, remark
) VALUES (
    '数据资产管理', 0, 5, 'data', '',
    '', 1, 0, 'M', '0',
    '0', '', 'data-asset', 'admin', datetime('now'),
    '数据资产管理模块'
);

-- 获取刚创建的菜单ID
SET @parent_id = LAST_INSERT_ID();

-- 创建二级菜单
INSERT INTO sys_menu (
    menu_name, parent_id, order_num, path, component,
    route_name, is_frame, is_cache, menu_type, visible,
    status, perms, icon, create_by, create_time, remark
) VALUES
('数据资产概览', @parent_id, 1, 'asset', 'data/asset/index',
 'DataAssetIndex', 0, 0, 'C', '0',
 '0', 'system:user:list', 'dashboard', 'admin', datetime('now'),
 '数据资产管理主页'),
('数据源管理', @parent_id, 2, 'datasource', 'data/asset/datasource/index',
 'DataSource', 0, 0, 'C', '0',
 '0', 'system:datasource:list', 'table', 'admin', datetime('now'),
 '数据源管理页面'),
('元数据浏览', @parent_id, 3, 'metadata', 'data/asset/metadata/index',
 'DataAssetMetadata', 0, 0, 'C', '0',
 '0', 'system:datasource:list', 'list', 'admin', datetime('now'),
 '元数据浏览页面'),
('表血缘管理', @parent_id, 4, 'lineage', 'data/asset/lineage/index',
 'TableLineage', 0, 0, 'C', '0',
 '0', 'system:datasource:list', 'tree-table', 'admin', datetime('now'),
 '表血缘管理页面（新功能）');
```

---

## 生产部署

### 后端部署

#### 1. 使用 Gunicorn

```bash
cd backend

# 安装 gunicorn
uv pip install gunicorn

# 运行
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

#### 2. 使用 Uvicorn（ASGI）

```bash
cd backend

# 安装 uvicorn
uv pip install uvicorn

# 运行
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 3
```

#### 3. 使用 Supervisor（推荐）

创建配置文件 `/etc/supervisor/conf.d/data-admin.conf`：

```ini
[program:data-admin]
directory=/path/to/data-admin/backend
command=/path/to/backend/.venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/data-admin.log
```

启动服务：

```bash
supervisorctl reread
supervisorctl update
supervisorctl start data-admin
```

### 前端部署

#### 1. 构建生产版本

```bash
cd frontend

# 构建生产版本
pnpm build:prod

# 构建产物在 dist/ 目录
```

#### 2. 复制到后端静态文件目录

```bash
# 创建后端静态文件目录
mkdir -p backend/dist

# 复制构建产物
cp -r frontend/dist/* backend/dist/
```

#### 3. 配置 Nginx

创建 Nginx 配置文件：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/data-admin/backend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /data-api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

重启 Nginx：

```bash
nginx -t
nginx -s reload
```

---

## 数据库配置

### MySQL 配置

编辑 `backend/config/settings.py`：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'data_admin',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

安装 MySQL 驱动：

```bash
uv pip install mysqlclient
# 或
uv pip install PyMySQL
```

### PostgreSQL 配置

编辑 `backend/config/settings.py`：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'data_admin',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

安装 PostgreSQL 驱动：

```bash
uv pip install psycopg2-binary
```

---

## 环境变量配置

### 后端环境变量

创建 `.env` 文件在 `backend/` 目录：

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=data_admin
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
```

### 前端环境变量

编辑 `frontend/.env.production`：

```bash
# API 基础路径
VITE_APP_BASE_API=/data-api/

# 应用标题
VITE_APP_TITLE=Data Admin

# 端口
VITE_PORT=5173
```

---

## 数据迁移

### 从旧版本迁移数据资产模块

```bash
cd backend
source .venv/bin/activate

# 1. 试运行模式（不实际修改数据）
python manage.py migrate_from_legacy --dry-run

# 2. 正式迁移
python manage.py migrate_from_legacy
```

### 迁移顺序

1. DataSource（`sys_datasource` → `dataasset_datasource`）
2. MetaTable（`datameta_table` → `dataasset_meta_table`）
3. MetaColumn（`datameta_column` → `dataasset_meta_column`）
4. MetaCollectionTask（`datameta_collection_task` → `dataasset_collection_task`）

---

## 验证安装

### 后端验证

```bash
cd backend
source .venv/bin/activate

# 检查项目配置
python manage.py check

# 运行测试
python manage.py test

# 检查数据库
python manage.py shell
>>> from apps.system.models import User
>>> User.objects.count()
1
```

### 前端验证

```bash
cd frontend
pnpm build:prod

# 检查构建产物
ls -la dist/
```

### 功能验证

1. 访问 `http://your-domain.com`
2. 使用 admin/admin123 登录
3. 检查左侧菜单是否显示"数据资产管理"
4. 测试各功能模块：
   - 数据源管理
   - 元数据浏览
   - 表血缘管理

---

## 性能优化

### 后端优化

1. **数据库连接池**
   ```bash
   uv pip install django-db-geventpool
   ```

2. **缓存配置**
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

3. **静态文件服务**
   ```bash
   python manage.py collectstatic --noinput
   ```

### 前端优化

1. **启用 Gzip 压缩**
   ```javascript
   // vite.config.js
   export default defineConfig({
       build: {
           brotliSize: true,
           chunkSizeWarningLimit: 1000
       }
   })
   ```

2. **CDN 加速**
   - 将静态资源上传到 CDN
   - 配置 CDN 域名

---

## 监控与日志

### 后端日志

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/data-admin/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 前端错误监控

集成 Sentry：

```bash
pnpm add @sentry/vue
```

```javascript
// main.js
import * as Sentry from "@sentry/vue"

Sentry.init({
  app,
  dsn: "your-sentry-dsn",
  environment: import.meta.env.MODE,
})
```

---

## 故障排查

### 问题 1：数据库连接失败

**解决方案：**
1. 检查数据库服务是否运行
2. 验证连接配置是否正确
3. 确认数据库用户权限

### 问题 2：前端页面空白

**解决方案：**
1. 检查控制台错误
2. 确认 API 路径配置正确
3. 清除浏览器缓存

### 问题 3：菜单不显示

**解决方案：**
1. 检查菜单的 `visible` 和 `status` 字段
2. 确认用户角色有相应权限
3. 重新登录刷新权限

### 问题 4：静态文件 404

**解决方案：**
1. 运行 `python manage.py collectstatic`
2. 检查 Nginx 静态文件配置
3. 确认文件权限正确

---

## 安全建议

1. **修改默认密码**
   - 登录后立即修改 admin 密码

2. **配置 HTTPS**
   - 使用 Let's Encrypt 获取免费证书
   - 强制 HTTPS 重定向

3. **限制访问**
   - 配置防火墙规则
   - 使用 fail2ban 防止暴力破解

4. **定期备份**
   - 数据库备份
   - 配置文件备份

5. **更新依赖**
   - 定期更新 Python 包
   - 定期更新 Node.js 包

---

## 维护指南

### 日常维护

```bash
# 数据库备份
python manage.py dumpdata > backup.json

# 清理会话
python manage.py clearsessions

# 清理缓存
python manage.py cache_clear
```

### 日志清理

```bash
# 日志轮转配置
/var/log/data-admin/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

---

**文档版本**: v1.0.0
**最后更新**: 2025-02-05
**维护者**: Data Admin 开发团队
