# 数据资产管理模块

## 概述

数据资产管理模块是 Data Admin 平台的核心模块之一，负责数据源管理、元数据采集、表血缘追踪等功能。该模块在 v1.0 版本中完成了重大重构，将原有的 `datasource` 和 `datameta` 应用整合为统一的 `dataasset` 应用，并新增了表血缘追踪功能。

---

## 功能特性

### 1. 数据源管理

支持多种数据库类型的连接配置与管理：
- MySQL、PostgreSQL、SQLite
- Oracle、SQL Server
- Presto、StarRocks

**核心功能：**
- 数据源 CRUD 操作
- 连接健康检查
- 批量删除支持
- 连接参数自定义（JSON/KV 格式）
- **数据源详情查看** ⭐新增：实时浏览数据源内容
  - 查看数据库列表（支持搜索）
  - 查看表列表（支持搜索）
  - 查看字段详情（支持搜索）
  - 整库元数据采集
  - 单表元数据采集

### 2. 元数据管理

**元数据采集：**
- 自动采集数据库、表、字段信息
- 支持同步采集（小数据量）
- 支持异步采集（大数据量）
- 采集任务状态跟踪

**元数据浏览：**
- 表查找模式：浏览所有表及详情
- 字段查找模式：跨表搜索字段
- 多条件过滤（数据源、表名、字段名、描述）

### 3. 表血缘追踪 ⭐新增

**血缘关系管理：**
- 手动配置表级血缘关系
- 支持上游（upstream）和下游（downstream）关系
- 血缘关系 CRUD 操作
- 批量删除支持

**血缘分析：**
- 递归查询上游/下游依赖
- 可视化血缘关系图
- 支持 1-5 层深度查询
- 影响分析

---

## 架构设计

### 数据模型

```
DataSource (数据源)
  ├─ 1 → N → MetaTable (元数据表)
  │                 ├─ 1 → N → MetaColumn (元数据字段)
  │                 └─ 1 → N → TableLineage (源表)
  └─ 1 → N → MetaCollectionTask (采集任务)

MetaTable (元数据表)
  ├─ N → 1 → DataSource
  ├─ 1 → N → MetaColumn
  ├─ 1 → N → TableLineage (源表)
  └─ 1 → N → TableLineage (目标表)

TableLineage (表血缘)
  ├─ N → 1 → MetaTable (源表) [source_table]
  ├─ N → 1 → MetaTable (目标表) [target_table]
  └─ 字段: lineage_type (upstream/downstream), description
```

### 数据库表

| 表名 | 模型 | 说明 |
|------|------|------|
| `dataasset_datasource` | DataSource | 数据源连接配置 |
| `dataasset_meta_table` | MetaTable | 元数据表 |
| `dataasset_meta_column` | MetaColumn | 元数据字段 |
| `dataasset_collection_task` | MetaCollectionTask | 元数据采集任务 |
| `dataasset_table_lineage` | TableLineage | 表血缘关系 |

---

## API 端点

### 基础规则

- **基础路径**: `/data-api/dataasset/`
- **认证**: JWT Token (Bearer)
- **响应格式**: JSON
- **分页参数**: `pageNum`, `pageSize`

### 数据源管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/datasource/` | GET | 数据源列表 |
| `/datasource/` | POST | 创建数据源 |
| `/datasource/{id}/` | GET | 数据源详情 |
| `/datasource/{id}/` | PUT | 更新数据源 |
| `/datasource/{id}/` | DELETE | 删除数据源 |
| `/datasource/{id}/test/` | POST | 测试连接（按ID） |
| `/datasource/test/` | POST | 测试连接（按请求体） |

### 元数据管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/meta-table/` | GET | 元数据表列表 |
| `/meta-table/` | POST | 创建元数据表 |
| `/meta-table/{id}/` | GET | 元数据表详情 |
| `/meta-table/{id}/` | PUT | 更新元数据表 |
| `/meta-table/{id}/` | DELETE | 删除元数据表 |
| `/meta-column/` | GET | 元数据字段列表 |
| `/meta-column/{id}/` | GET | 字段详情 |
| `/meta-column/{id}/` | PUT | 更新字段 |
| `/meta-column/{id}/` | DELETE | 删除字段 |

### 元数据采集

| 端点 | 方法 | 说明 |
|------|------|------|
| `/collection/databases/` | POST | 获取数据库列表 |
| `/collection/tables/` | POST | 获取表列表 |
| `/collection/columns/` | POST | 获取字段列表 |
| `/collection/collect/` | POST | 同步采集（整库） |
| `/collection/collect-table/` | POST | 单表采集 ⭐新增 |
| `/collection/collect-async/` | POST | 异步采集（整库）⭐增强 |
| `/collection/collect-status/` | GET | 采集任务状态 ⭐新增 |
| `/collection/collect-cancel/` | POST | 取消采集任务 ⭐新增 |

#### 异步采集 API 说明

**1. 启动异步采集任务**

```http
POST /data-api/dataasset/collection/collect-async/
Content-Type: application/json

{
  "dataSourceId": 1,
  "databaseName": "my_database"
}
```

**响应：**
```json
{
  "code": 200,
  "msg": "任务已启动",
  "data": {
    "taskId": "collect_task_1234567890"
  }
}
```

**2. 查询任务状态**

```http
GET /data-api/dataasset/collection/collect-status/?taskId=collect_task_1234567890
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "taskId": "collect_task_1234567890",
    "status": "running",
    "current": 25,
    "total": 100,
    "error": null
  }
}
```

**状态说明：**
- `running` - 运行中
- `completed` - 已完成
- `failed` - 失败
- `cancelled` - 已取消

**3. 取消采集任务**

```http
POST /data-api/dataasset/collection/collect-cancel/
Content-Type: application/json

{
  "taskId": "collect_task_1234567890"
}
```

**响应：**
```json
{
  "code": 200,
  "msg": "任务已取消"
}
```

### 表血缘管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/lineage/` | GET | 血缘关系列表 |
| `/lineage/` | POST | 创建血缘关系 |
| `/lineage/{id}/` | GET | 血缘详情 |
| `/lineage/{id}/` | PUT | 更新血缘关系 |
| `/lineage/{id}/` | DELETE | 删除血缘关系 |
| `/lineage/upstream/` | GET | 查询上游血缘 |
| `/lineage/downstream/` | GET | 查询下游血缘 |
| `/lineage/graph/` | GET | 生成血缘关系图 |

### 响应格式

**成功响应：**
```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {...}
}
```

**列表响应：**
```json
{
  "code": 200,
  "msg": "操作成功",
  "total": 100,
  "pageNum": 1,
  "pageSize": 10,
  "rows": [...]
}
```

**错误响应：**
```json
{
  "code": 400/404/500,
  "msg": "错误信息"
}
```

---

## 前端实现

### 组件结构

```
frontend/src/views/data/asset/
├── index.vue                 # 数据资产管理主页（仪表板）
├── datasource/
│   ├── index.vue             # 数据源管理页面
│   └── detail.vue            # 数据源详情页面 ⭐新增
├── metadata/
│   └── index.vue             # 元数据浏览页面
└── lineage/
    └── index.vue             # 表血缘管理页面
```

### API 封装

统一的 API 文件：`frontend/src/api/data/asset.js`

```javascript
// 数据源相关
import {
  listDatasource,
  addDatasource,
  updateDatasource,
  delDatasource,
  testDatasource
} from '@/api/data/asset'

// 元数据相关
import {
  listMetaTables,
  listMetaColumns,
  collectMeta,
  collectMetaAsync
} from '@/api/data/asset'

// 血缘相关
import {
  listTableLineage,
  addTableLineage,
  getLineageGraph
} from '@/api/data/asset'
```

### 页面功能

#### 1. 数据资产主页 (`index.vue`)

**统计卡片：**
- 数据源总数（点击跳转）
- 元数据表总数（点击跳转）
- 元数据字段总数（点击跳转）
- 血缘关系总数（点击跳转）

**功能导航：**
- 数据源管理
- 元数据浏览
- 血缘管理

#### 2. 数据源管理 (`datasource/index.vue`)

**操作流程：**
1. 新增数据源 → 选择数据库类型
2. 填写连接信息 → 测试连接
3. 保存 → 列表中查看

**支持的数据库：**
- MySQL
- PostgreSQL
- SQLite
- Oracle
- SQL Server
- Presto
- StarRocks

#### 2.5. 数据源详情 (`datasource/detail.vue`) ⭐新增

**页面功能：**
- **数据源基本信息**：显示数据源的连接配置、状态、创建时间等
- **数据库列表浏览**：
  - 实时查询数据源下的所有数据库
  - 支持按数据库名称搜索（前端过滤）
  - 查看表列表：点击"查看表"按钮
  - 整库采集：点击"采集"按钮启动异步采集任务
- **数据表列表浏览**：
  - 显示选中数据库的所有表
  - 支持按表名、表描述搜索（前端过滤）
  - 查看字段详情：点击"查看字段"按钮
  - 单表采集：点击"采集"按钮采集单个表的元数据
- **字段详情对话框**：
  - 显示表的所有字段信息
  - 支持按字段名、字段描述搜索（前端过滤）
  - 字段信息：序号、字段名、数据类型、键类型、可空性、默认值等

**异步采集功能：**
- **实时进度显示**：
  - 进度条显示采集百分比
  - 状态显示：运行中、已完成、失败、已取消
  - 统计信息：已采集表数/总表数
  - 错误提示：失败时显示详细错误信息
- **任务控制**：
  - 取消按钮：可随时取消正在运行的采集任务
  - 按钮状态：采集中显示"采集中..."并禁用
  - 完成提示：成功/失败/取消时显示相应消息
- **状态持久化**：
  - 任务完成后保留状态显示
  - 支持重新采集（覆盖之前状态）

**实现特点：**
- 数据实时查询：所有信息直接从数据源获取，不依赖元数据库
- 前端搜索过滤：使用 Vue computed 属性实现实时过滤
- 路由参数监听：自动处理不同数据源切换时的数据重载
- 响应式设计：数据库/表/字段三层级联展示
- 异步任务管理：使用定时器轮询任务状态（2秒间隔）
- 用户体验优化：大数据库采集不会超时，支持中途取消

#### 3. 元数据浏览 (`metadata/index.vue`)

**双模式切换：**
- 表查找模式：浏览所有表
- 字段查找模式：跨表搜索字段

**元数据采集：**
- 快速采集：通过元数据浏览页批量采集
- 详细采集：通过数据源详情页进行异步采集（推荐）
  - 支持整库采集和单表采集
  - 实时显示采集进度
  - 支持取消任务
- 进度跟踪：自动更新采集状态

#### 4. 表血缘管理 (`lineage/index.vue`)

**血缘类型：**
- 上游（upstream）：数据来源表
- 下游（downstream）：数据目标表

**血缘图：**
- 可视化展示血缘网络
- 支持 1-5 层深度查询
- 区分上游/下游关系

---

## 使用指南

### 添加数据源

1. 进入"数据源管理"
2. 点击"新增"按钮
3. 选择数据库类型（如 MySQL）
4. 填写连接信息：
   - 主机地址
   - 端口号
   - 数据库名
   - 用户名
   - 密码
   - 连接参数（可选）
5. 点击"测试连接"
6. 连接成功后点击"确定"

### 查看数据源详情 ⭐新增

1. 进入"数据源管理"
2. 点击数据源行的"查看"按钮
3. 进入数据源详情页面，包含以下功能：
   - **数据库列表**：
     - 自动加载数据源下的所有数据库
     - 搜索框：输入数据库名称快速过滤
     - 点击"查看表"：查看该数据库下的所有表
     - 点击"采集"：整库采集元数据到元数据库
   - **数据表列表**：
     - 显示选中数据库的所有表
     - 搜索框：输入表名或表描述快速过滤
     - 点击"查看字段"：弹出对话框查看表字段详情
     - 点击"采集"：单表采集元数据到元数据库
   - **字段详情**：
     - 对话框形式展示表的所有字段
     - 搜索框：输入字段名或描述快速过滤
     - 显示字段序号、类型、键类型、可空性等信息

### 采集元数据

**方式一：通过数据源详情页采集（推荐）**

1. 进入"数据资产管理" → "数据源管理"
2. 点击目标数据源行的"查看"按钮
3. 在数据源详情页面进行采集：

**整库采集（异步）：**
1. 在数据库列表中找到目标数据库
2. 点击"采集"按钮
3. 确认采集对话框
4. 任务启动后会显示：
   - **进度条**：实时显示采集进度百分比
   - **状态提示**：运行中、已完成、失败、已取消
   - **统计信息**：已采集表数/总表数
5. 可选操作：
   - 点击"取消"标签：中途取消采集任务
6. 采集完成后：
   - 成功：显示绿色成功标签和采集表数
   - 失败：显示红色失败标签和错误原因
   - 可重新采集（会覆盖之前状态）

**单表采集（同步）：**
1. 在数据库列表中点击"查看表"
2. 在表列表中找到目标表
3. 点击"采集"按钮
4. 等待采集完成（单表采集通常很快）

**方式二：通过元数据浏览页采集**

1. 进入"元数据浏览"
2. 点击"元数据采集"按钮
3. 选择数据源和数据库名称（可选）
4. 点击"开始采集"
5. 刷新页面查看采集结果

**异步采集的优势：**
- ✅ 不会超时：适合包含大量表的大型数据库
- ✅ 实时反馈：显示采集进度和状态
- ✅ 可中断：支持中途取消不需要等待
- ✅ 错误提示：失败时显示详细错误信息

### 配置表血缘

1. 进入"血缘管理"
2. 点击"新增血缘"
3. 选择源表（数据来源）
4. 选择目标表（数据目标）
5. 选择血缘类型（上游/下游）
6. 填写描述（可选）
7. 点击"确定"

### 查看血缘图

1. 进入"血缘管理"
2. 点击"血缘图"按钮
3. 选择要查询的表
4. 设置查询深度（建议 2-3 层）
5. 点击"刷新"
6. 查看血缘关系网络

---

## 路由配置

### 方式 1：使用 Django 命令（推荐）

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

### 方式 2：手动执行 SQL

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
    '0', '', 'database', 'admin', datetime('now'),
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
 '0', 'system:datasource:list', 'share', 'admin', datetime('now'),
 '表血缘管理页面（新功能）');
```

---

## 数据迁移

### 从旧版本迁移

```bash
# 1. 试运行模式（不实际修改数据）
cd backend
source .venv/bin/activate
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

## 权限说明

### 菜单权限标识

| 菜单 | 权限标识 | 说明 |
|------|---------|------|
| 数据资产概览 | `system:user:list` | 所有用户可访问 |
| 数据源管理 | `system:datasource:list` | 查看数据源列表 |
| 数据源新增 | `system:datasource:add` | 新增数据源 |
| 数据源修改 | `system:datasource:edit` | 修改/测试数据源 |
| 数据源删除 | `system:datasource:remove` | 删除数据源 |
| 元数据浏览 | `system:datasource:list` | 浏览元数据 |
| 表血缘管理 | `system:datasource:list` | 管理血缘关系 |

**注意：** admin 用户拥有所有权限，其他用户需要分配相应权限。

---

## 关键文件位置

### 后端文件

```
backend/apps/dataasset/
├── __init__.py
├── apps.py
├── models.py              # 5个数据模型
├── serializers.py         # 所有序列化器
├── views.py               # 所有 ViewSet
├── urls.py                # URL 路由配置
├── collectors.py          # 异步采集执行器
├── admin.py               # Django admin 配置
└── management/commands/
    ├── migrate_from_legacy.py  # 数据迁移命令
    └── add_dataasset_menu.py   # 菜单添加命令
```

### 前端文件

```
frontend/src/
├── api/data/
│   └── asset.js               # 统一 API 封装
├── router/
│   └── index.js               # 路由配置（包含数据源详情路由）
└── views/data/asset/
    ├── index.vue              # 主页（仪表板）
    ├── datasource/
    │   ├── index.vue          # 数据源管理
    │   └── detail.vue         # 数据源详情 ⭐新增
    ├── metadata/index.vue     # 元数据浏览
    └── lineage/index.vue      # 表血缘管理
```

### 配置文件

```
backend/config/
├── settings.py            # 已更新 INSTALLED_APPS
└── urls.py                # 已添加 dataasset 路由
```

---

## 版本历史

### v1.0.1 (2025-02-05)

**新增功能：**
- ✅ 数据源详情页面（`detail.vue`）
  - 实时浏览数据源的数据库、表、字段信息
  - 前端搜索过滤功能
  - 整库元数据采集按钮（异步）⭐增强
  - 单表元数据采集按钮
- ✅ 异步元数据采集功能 ⭐重大改进
  - 实时进度显示（进度条、状态、统计信息）
  - 任务状态轮询（每2秒更新一次）
  - 支持取消正在运行的采集任务
  - 错误提示和状态持久化
  - 解决大数据库采集超时问题
- ✅ 新增异步采集 API：
  - `/collection/collect-async/` - 启动异步采集任务
  - `/collection/collect-status/` - 查询任务状态
  - `/collection/collect-cancel/` - 取消采集任务
- ✅ 新增单表采集 API（`/collection/collect-table/`）
- ✅ 数据源管理"查看"按钮跳转到详情页

**技术改进：**
- Vue 3 Composition API + 响应式任务状态管理
- 定时器轮询机制实现任务状态实时更新
- Element Plus 进度条和标签组件展示采集状态
- 用户体验优化：解决超时、提供进度反馈、支持中断操作

**技术改进：**
- Vue 3 Composition API 最佳实践
- Computed 属性实现响应式搜索过滤
- Watch 监听路由参数变化
- 组件状态管理优化
- 修复 Vue 警告（el-tag type prop、v-loading 指令）

### v1.0.0 (2025-02-04)

**重大重构：**
- ✅ 整合 `datasource` 和 `datameta` 应用到 `dataasset`
- ✅ 新增表血缘追踪功能
- ✅ 统一 API 端点到 `/dataasset/`
- ✅ 实现异步元数据采集
- ✅ 完成前后端完整实现
- ✅ 通过全部测试（11/11）

**新增功能：**
- ⭐ 表级血缘管理
- ⭐ 血缘关系图可视化
- ⭐ 统一的数据资产入口

**技术改进：**
- Vue 3 Composition API
- Element Plus UI 组件
- 响应式设计
- 渐变色动画

---

## 后续扩展计划

### 短期优化
1. 增强血缘可视化（使用专业图表库）
2. 添加字段级血缘追踪
3. 实现自动血缘解析
4. 数据地图功能
5. 元数据质量报告

### 长期规划
1. 血缘影响分析
2. 血缘版本管理
3. 自动血缘发现（从 ETL 配置）
4. 数据资产画像
5. 智能推荐引擎

---

**文档版本**: v1.0.1
**最后更新**: 2025-02-05
**维护者**: Data Admin 开发团队
