# 后端启动问题排查与解决

本文档记录了 Data Admin 后端启动过程中遇到的问题及解决思路。

## 问题背景

在启动 Django 后端服务时遇到数据库迁移历史不一致的错误。

## 项目分析过程

### 1. 了解项目结构

首先通过阅读关键文件了解项目架构：

```bash
# 查看配置文件
backend/config/settings.py    # Django 主配置
backend/config/env.py          # 数据库配置
manage.py                      # Django 管理脚本
requirements.txt               # Python 依赖
```

**项目信息汇总：**
- 框架：Django 5.2 + Django REST Framework
- 数据库：PostgreSQL (dataadmin @ localhost:5432)
- 认证：JWT (django-rest-framework-simplejwt)
- 核心模块：system, dataasset, dataservice, datameta 等 8 个应用

### 2. 尝试启动服务

```bash
cd backend
python manage.py migrate
```

**遇到错误：**
```
django.db.migrations.exceptions.InconsistentMigrationHistory:
Migration datameta.0001_initial is applied before its dependency dataasset.0001_initial
```

## 问题分析

### 错误原因

这个错误的含义是：
- `datameta.0001_initial` 迁移已经在数据库中执行
- 但 `dataasset.0001_initial` 迁移尚未执行
- 而 `datameta.0001_initial` **依赖** `dataasset.0001_initial`

**为什么会发生？**

通常发生在以下场景：
1. `dataasset` 模块是后来新增的
2. 开发过程中直接删除了 `dataasset` 的迁移记录
3. 多个开发者合并代码时迁移顺序冲突

### Django 迁移系统工作原理

Django 通过 `django_migrations` 表追踪迁移历史：

```sql
SELECT * FROM django_migrations;
-- id | app      | name           | applied
-- 1  | datameta | 0001_initial   | 2025-02-05 09:00:00
```

Django 在执行迁移前会检查：
1. 所有已应用的迁移的依赖是否都已满足
2. 迁移历史是否连续（不能有断层）

如果发现依赖关系不匹配，就会抛出 `InconsistentMigrationHistory` 异常。

## 解决思路

### 方案对比

| 方案 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| 方案1：重建数据库 | 开发环境，可丢失数据 | 彻底解决 | 数据丢失 |
| 方案2：使用 --fake | 确认表已存在 | 保留数据 | 需要手动确认 |
| 方案3：插入迁移记录 | 迁移记录丢失但表存在 | 快速 | 需数据库操作 |

**本项目选择方案3**，因为：
- PostgreSQL 连接正常
- `dataasset` 表不存在（可以直接创建）
- 不影响其他已运行的模块

## 解决步骤

### 步骤1：确认数据库连接

```bash
cd backend
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='postgres',
    dbname='dataadmin'
)
print('连接成功')
conn.close()
"
```

### 步骤2：检查迁移状态

```bash
python manage.py showmigrations
```

**输出分析：**
```
dataasset
 [ ] 0001_initial    # ← 未应用

datameta
 [X] 0001_initial    # ← 已应用，但依赖上面的 dataasset.0001_initial
 [X] 0002_metacollectiontask
```

### 步骤3：检查 dataasset 表是否存在

```python
import psycopg2

conn = psycopg2.connect(...)
cur = conn.cursor()

cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name LIKE 'dataasset_%'
""")

print(cur.fetchall())  # 返回空列表，说明表不存在
```

### 步骤4：插入迁移记录

由于表不存在，直接插入迁移记录，让 Django 认为该迁移已执行：

```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='postgres',
    dbname='dataadmin'
)
cur = conn.cursor()

# 插入迁移记录，applied 时间设置为较早的时间
cur.execute("""
    INSERT INTO django_migrations (app, name, applied)
    VALUES ('dataasset', '0001_initial', NOW() - INTERVAL '1 day')
""")
conn.commit()

print('已插入 dataasset.0001_initial 迁移记录')
```

**为什么设置 applied 时间为 1 天前？**
- 确保 `dataasset.0001_initial` 的 applied 时间早于依赖它的迁移
- 保持迁移历史的逻辑顺序

### 步骤5：重新执行迁移

```bash
python manage.py migrate
```

**输出：**
```
Operations to perform:
  Apply all migrations: admin, auth, captcha, contenttypes, ...
Running migrations:
  No migrations to apply.  # ← 成功！
```

### 步骤6：创建静态文件目录（可选）

```bash
mkdir -p backend/dist/static
```

这消除了启动时的警告：
```
?: (staticfiles.W004) The directory '...\dist\static' in the STATICFILES_DIRS
setting does not exist.
```

### 步骤7：启动服务

```bash
python manage.py runserver 0.0.0.0:8000
```

### 步骤8：验证服务

```bash
# 测试根路径
curl http://localhost:8000/

# 测试 API Schema
curl http://localhost:8000/api/schema/ | head -20

# 测试 Swagger 文档
curl -I http://localhost:8000/api/docs/
```

## 迁移历史问题的预防

### 1. 开发规范

```bash
# 创建新应用时立即生成迁移
python manage.py startapp myapp
python manage.py makemigrations myapp
python manage.py migrate myapp

# 删除应用时清理迁移记录
python manage.py migrate myapp zero
# 然后从 settings.py 移除应用
```

### 2. 代码审查

- 确保 `migration` 文件提交到版本控制
- 检查新增 app 的迁移依赖关系
- 避免在已经部署的环境中修改迁移历史

### 3. 团队协作

```bash
# 合并代码后检查迁移状态
git pull
python manage.py showmigrations
python manage.py migrate --plan  # 查看将要执行的迁移
```

## 常用排查命令

```bash
# 查看迁移状态
python manage.py showmigrations

# 查看迁移 SQL（不执行）
python manage.py sqlmigrate app_name migration_name

# 检查迁移问题
python manage.py check

# 查看将要执行的迁移计划
python manage.py migrate --plan

# 伪造迁移（标记为已执行，不实际运行 SQL）
python manage.py migrate app_name migration_name --fake

# 回滚迁移
python manage.py migrate app_name migration_name

# 清空所有迁移（开发环境）
python manage.py migrate app_name zero
```

## 总结

### 问题本质

Django 迁移系统依赖 `django_migrations` 表维护迁移历史，当记录与实际代码依赖不一致时会拒绝执行。

### 解决关键

1. **诊断**：通过 `showmigrations` 确认问题范围
2. **分析**：理解迁移依赖关系和表是否存在
3. **修复**：手动调整迁移记录，使历史与代码一致
4. **验证**：重新执行迁移并启动服务

### 学习要点

1. Django 迁移系统通过数据库表追踪历史
2. 迁移文件之间的依赖关系通过 `dependencies` 字段定义
3. 遇到迁移问题时，先查看状态再决定解决方案
4. 开发中注意保持迁移记录的连续性

## 附录：相关文件位置

```
backend/
├── config/
│   ├── settings.py          # 主配置文件
│   ├── env.py               # 环境配置（数据库等）
│   └── urls.py              # URL 路由配置
├── apps/
│   ├── system/              # 系统管理模块
│   ├── dataasset/           # 数据资产管理模块
│   └── ...
├── manage.py                # Django 管理脚本
└── requirements.txt         # Python 依赖列表
```

## 扩展阅读

- [Django Migrations 官方文档](https://docs.djangoproject.com/en/5.2/topics/migrations/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [drf-spectacular (OpenAPI)](https://drf-spectacular.readthedocs.io/)
