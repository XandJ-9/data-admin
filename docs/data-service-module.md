# 数据服务模块

## 概述

数据服务模块（DataService）是 Data Admin 平台的数据消费层，负责为外部系统提供统一的数据查询服务、数据接口管理和数据导出功能。该模块作为平台数据的最终出口，连接了数据仓库与业务应用，实现了数据的快速查询、灵活接口和便捷导出。

---

## 功能特性

### 1. SQL 查询服务

**核心能力：**
- 多数据源支持：MySQL、PostgreSQL、Oracle、SQL Server、SQLite 等
- 动态 SQL 模板：支持 Django Template 语法的参数化查询
- 分页查询：支持 pageSize 和 offset 参数的分页控制
- 查询超时保护：默认 60 秒超时限制
- 结果导出：一键导出为 CSV 格式（BOM 头支持）

**查询流程：**
```
用户输入 SQL + 参数
    ↓
前端发送请求（dataSourceId + sql + params）
    ↓
后端验证并渲染 SQL（Django Template）
    ↓
连接数据源执行查询
    ↓
返回结果（columns + rows）
    ↓
前端展示表格或导出 CSV
```

### 2. 数据接口管理

**接口定义：**
- 接口基本信息：接口名称、编码、描述、所属报表
- SQL 配置：查询 SQL、合计 SQL（可选）
- 功能开关：分页、合计、日期查询、二级表头、登录验证
- 报表归属：平台名称、模块名称、报表编码
- 数据源关联：支持动态切换数据源

**接口字段配置：**
- 输入/输出参数：支持定义查询条件和返回字段
- 字段类型：字符、整数、小数、百分比、日期等 15 种类型
- 显示控制：是否显示、是否导出、显示描述
- 级联参数：支持下拉框级联选择
- 二级表头：支持字段跨行展示

### 3. 元数据管理

**接口元数据导入导出：**
- Excel 批量导入：支持批量创建/更新接口定义
- Excel 导出：样式化的接口定义文档
- 字段自动排序：新增/删除/修改字段时自动调整位置

### 4. 查询审计

**完整的查询日志：**
- 执行用户记录
- SQL 语句记录（包含渲染后的 SQL）
- 执行状态（成功/失败）
- 执行耗时（毫秒级）
- 错误信息记录
- 查询类型区分（SQL 查询 / 接口查询）

### 5. 查询日志管理

**日志查询和筛选：**
- 按用户名筛选
- 按执行状态筛选（成功/失败）
- 支持分页查看
- SQL 详情查看（长SQL支持弹窗查看完整内容）
- 错误信息提示（Tooltip显示完整错误信息）

**页面功能：**
- 实时查询日志列表
- 表格展示所有查询记录
- 状态标签（成功/失败）
- 执行耗时统计
- 查询类型标识
- SQL 文本展示（超过100字显示省略号）

---

## 架构设计

### 数据模型

```
QueryLog (查询日志)
  └─ N → 1 → DataSource (数据源)

InterfaceInfo (接口信息)
  ├─ N → 1 → DataSource (数据源)
  └─ 1 → N → InterfaceField (接口字段)

InterfaceField (接口字段)
  └─ N → 1 → InterfaceInfo (接口)
```

### 数据库表

| 表名 | 模型 | 说明 |
|------|------|------|
| `dataservice_query_log` | QueryLog | 数据查询日志 |
| `dataservice_interface_info` | InterfaceInfo | 数据接口信息 |
| `dataservice_interface_field` | InterfaceField | 数据接口字段 |

---

## API 端点

### 基础规则

- **基础路径**: `/data-api/dataservice/`
- **认证**: JWT Token (Bearer)
- **响应格式**: JSON
- **分页参数**: `pageNum`, `pageSize`

### SQL 查询服务

| 端点 | 方法 | 说明 |
|------|------|------|
| `/query` | POST | 执行 SQL 查询 |
| `/export` | POST | 导出查询结果为 CSV |

**请求参数：**
```json
{
  "dataSourceId": 1,
  "sql": "SELECT * FROM users WHERE status = '{{status}}'",
  "params": {
    "status": "active"
  },
  "pageSize": 50,
  "offset": 0
}
```

**响应格式：**
```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "columns": ["id", "name", "email"],
    "rows": [
      [1, "Alice", "alice@example.com"],
      [2, "Bob", "bob@example.com"]
    ]
  }
}
```

### 查询日志管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/query-log/` | GET | 查询日志列表 |
| `/query-log/{id}` | GET | 查询日志详情 |

**查询参数：**
- `userName`: 按用户名过滤
- `status`: 按执行状态过滤（success/fail）

### 数据接口管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/interface-info/` | GET | 接口列表 |
| `/interface-info/` | POST | 新增接口 |
| `/interface-info/{id}` | GET | 接口详情 |
| `/interface-info/{id}` | PUT | 修改接口 |
| `/interface-info/{id}` | DELETE | 删除接口 |
| `/interface-info/{id}/execute` | POST | 执行接口查询 |
| `/interface-info/{id}/export` | POST | 导出接口数据 |
| `/interface-info/{id}/export-meta` | POST | 导出接口定义 Excel |
| `/interface-info/import-meta` | POST | 导入接口定义 Excel |

**查询参数：**
- `interfaceName`: 按接口名称过滤
- `interfaceCode`: 按接口编码过滤
- `interfaceDbType`: 按数据库类型过滤

### 接口字段管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/interface-field/` | GET | 接口字段列表 |
| `/interface-field/` | POST | 新增字段 |
| `/interface-field/{id}` | GET | 字段详情 |
| `/interface-field/{id}` | PUT | 修改字段 |
| `/interface-field/{id}` | DELETE | 删除字段 |

**查询参数：**
- `interfaceId`: 按接口 ID 过滤

---

## 前端实现

### 组件结构

```
frontend/src/views/data/service/
├── index.vue                    # 数据服务主页
├── query/
│   ├── index.vue                # SQL 查询页面 ⭐ v1.1.0 优化
│   ├── queryView.vue            # 查询编辑器视图
│   ├── queryResult.vue          # 查询结果展示
│   ├── queryLog.vue             # 查询日志
│   └── resizable-splitter.vue   # 可调整大小的分割面板 ⭐ v1.1.0 增强
├── interface/
│   ├── index.vue                # 接口管理页面
│   └── detail.vue               # 接口详情页面
└── report/
    └── index.vue                # 报表管理页面（规划中）
```

**组件说明：**

**query/index.vue（v1.1.0 主要优化）：**
- 多标签页管理
- 布局预设控制（编辑优先/均衡布局/结果优先）
- 响应式高度计算（设备适配）
- 窗口大小监听（防抖处理）
- 布局偏好持久化（localStorage）

**resizable-splitter.vue（v1.1.0 增强）：**
- 拖拽调整高度
- 视觉反馈（悬停/拖拽状态）
- Tooltip 提示
- 首次使用引导

### API 封装

统一的 API 文件：`frontend/src/api/data/service.js`

```javascript
// SQL 查询相关
import {
  executeQuery,
  exportQuery
} from '@/api/data/service'

// 接口管理相关
import {
  listInterfaceInfo,
  getInterfaceInfo,
  addInterfaceInfo,
  updateInterfaceInfo,
  delInterfaceInfo
} from '@/api/data/service'

// 接口字段相关
import {
  listInterfaceFields,
  addInterfaceField,
  updateInterfaceField,
  delInterfaceField
} from '@/api/data/service'

// 接口执行相关
import {
  executeInterfaceById,
  exportInterfaceById
} from '@/api/data/service'

// 元数据管理
import {
  exportInterfaceMeta,
  importInterfaceMeta
} from '@/api/data/service'
```

### 页面功能

#### 1. SQL 查询页面 (`query/index.vue`)

**功能特性：**
- **多标签页查询**：支持同时打开多个查询标签页
- **智能布局管理** ⭐：
  - **三种预设布局**：编辑优先（65:35）、均衡布局（50:50）、结果优先（35:65）
  - **手动调整**：拖拽分割条自定义编辑器和结果区高度
  - **记忆功能**：自动保存用户布局偏好到 localStorage
  - **响应式适配**：根据设备类型（移动/平板/桌面）智能调整高度
  - **窗口自适应**：窗口大小变化时自动调整布局，保持用户选择的比例
- **动态参数支持**：支持 Django Template 语法的参数化查询
  - 使用 `{{paramName}}` 占位符
  - 查询时弹出参数输入框
  - 参数自动渲染到 SQL 中
- **数据源选择**：下拉选择已配置的数据源
- **分页查询**：支持 pageSize 和 offset 参数
- **结果导出**：一键导出为 CSV（带 BOM 头）
- **编辑器增强**：
  - SQL 语法高亮
  - 代码自动补全
  - 放大编辑功能
  - 模板参数预览

**布局管理详解：**

**1. 预设布局按钮**
```
布局预设：[编辑优先] [均衡布局] [结果优先]
```
- **编辑优先**：适合编写复杂 SQL，编辑器占 65%
- **均衡布局**：默认布局，编辑器和结果区各 50%
- **结果优先**：适合查看大量数据，结果区占 65%

**2. 手动调整分割条**
- 位置：编辑器和结果区之间
- 视觉提示：
  - 悬停时高亮显示（蓝色边框）
  - 拖拽手柄居中显示
  - 首次使用显示"拖拽调整"提示
- 操作：鼠标悬停 → 光标变为上下箭头 → 按住拖拽
- 限制：
  - 编辑器最小高度：150px（移动端 120px）
  - 结果区最小高度：100px

**3. 响应式适配**
```javascript
// 设备断点
mobile:  < 768px   (移动端，默认结果优先)
tablet:  768-1024px (平板，默认均衡布局)
desktop: > 1024px  (桌面，默认均衡布局)

// 头部高度（自动调整）
移动端: 140px
平板:   160px
桌面:   180px

// 最小高度（自动调整）
移动端: 400px
平板:   450px
桌面:   500px
```

**4. 智能高度更新**
- **预设模式**：窗口变化时重新应用预设比例
- **自定义模式**：窗口变化时保持用户调整的比例
- **防抖处理**：200ms 防抖，避免频繁计算

**5. 布局持久化**
```javascript
// 保存用户偏好
localStorage.setItem('query-layout-preference', JSON.stringify({ mode: 'balanced' }))

// 新标签页自动应用
addTab() → 加载偏好 → 应用布局
```

**查询示例：**
```sql
-- 模板 SQL
SELECT * FROM users
WHERE status = '{{status}}'
  AND create_time >= '{{startDate}}'
  LIMIT 100

-- 渲染后 SQL
SELECT * FROM users
WHERE status = 'active'
  AND create_time >= '2025-01-01'
  LIMIT 100
```

#### 2. 接口管理页面 (`interface/index.vue`)

**核心功能：**
- **接口列表**：
  - 支持按接口名称、编码、数据库类型搜索
  - 显示接口所属平台、模块、报表
  - 显示接口状态（启用/禁用）
- **接口配置**：
  - 基本信息：接口名称、编码、描述
  - SQL 配置：查询 SQL、合计 SQL
  - 功能开关：分页、合计、日期查询、二级表头
  - 数据源关联：动态选择数据源
- **字段管理**：
  - 输入参数配置（查询条件）
  - 输出参数配置（返回字段）
  - 字段类型、显示、导出配置
  - 级联参数配置
- **接口测试**：
  - 在线测试接口执行
  - 查看返回结果
  - 导出测试数据

#### 3. 接口详情页面 (`interface/detail/index.vue`)

**详情展示：**
- 接口基本信息（15个字段）
  - 基本信息：接口名称、编码、数据库类型、数据库名称
  - 业务归属：平台名称、模块名称、报表名称、报表编码
  - 功能开关：分页、日期查询、合计、登录验证
  - 其他配置：报警类型、接口状态
- SQL 查看功能（语法高亮代码编辑器）
- 字段管理
  - 字段分类展示（请求参数 / 响应参数）
  - 字段 CRUD 操作（新增、修改、删除）
  - 15 种数据类型支持（字符、整数、小数、日期等）
  - 显示/导出配置
  - 二级表头支持（父级表头、合并行、显示备注）
- 导出接口定义（Excel 格式）

---

## 菜单初始化

数据服务模块需要初始化菜单后才能在前端显示。使用 Django 管理命令完成菜单初始化：

### 初始化菜单

```bash
# 进入 backend 目录
cd backend

# 运行菜单初始化命令
python manage.py add_dataservice_menu
```

**执行结果：**
```
============================================================
[添加] 开始添加数据服务管理菜单
============================================================
[步骤 1/4] 处理一级菜单...
   新建菜单
   创建成功！菜单ID: 12
[步骤 2/4] 处理 SQL 查询菜单...
   [成功] 处理完成
[步骤 3/4] 处理接口管理菜单...
   [成功] 处理完成
[步骤 4/4] 处理查询日志菜单...
   [成功] 处理完成
============================================================
[完成] 数据服务管理菜单添加完成！
============================================================

菜单结构：
  数据服务管理
  |-- SQL 查询
  |-- 接口管理
  |-- 查询日志
```

### 强制更新菜单

如果需要更新已存在的菜单配置，使用 `--force` 参数：

```bash
python manage.py add_dataservice_menu --force
```

### 菜单结构

初始化后会在系统中创建以下菜单：

| 菜单名称 | 菜单类型 | 路由路径 | 图标 | 说明 |
|---------|---------|----------|------|------|
| 数据服务管理 | 目录 | /data-service | server | 一级菜单 |
| SQL 查询 | 菜单 | query | code | SQL 查询页面 |
| 接口管理 | 菜单 | interface | guide | 接口管理页面 |
| 查询日志 | 菜单 | query-log | document | 查询日志页面 |

### 权限配置

菜单创建后，需要在"系统管理 → 角色管理"中为相应角色分配权限：

- `system:dataservice:query` - SQL 查询权限
- `system:dataservice:interface` - 接口管理权限
- `system:dataservice:querylog` - 查询日志权限

**注意：** admin 用户拥有所有权限，无需额外配置。

---

## 使用指南

### 执行 SQL 查询

1. 进入"数据服务" → "SQL 查询"
2. 在左侧编辑器输入 SQL 语句
3. （可选）添加动态参数：
   ```
   SELECT * FROM orders
   WHERE order_date >= '{{startDate}}'
     AND order_date <= '{{endDate}}'
   ```
4. 选择数据源
5. 点击"执行查询"
6. 如果有参数，会弹出参数输入框
7. 查看结果或导出 CSV

### 创建数据接口

1. 进入"数据服务" → "接口管理"
2. 点击"新增接口"
3. 填写基本信息：
   - 接口名称：订单查询接口
   - 接口编码：ORDER_QUERY（唯一）
   - 接口描述：查询订单信息
   - 所属报表：选择关联的报表（可选）
4. 配置 SQL：
   ```sql
   SELECT
     order_id,
     customer_name,
     order_amount,
     order_date
   FROM orders
   WHERE order_date >= '{{startDate}}'
     AND order_date <= '{{endDate}}'
   ```
5. 配置功能开关：
   - 是否分页：是
   - 是否合计：否
   - 是否日期查询：是
6. 选择数据源
7. 点击"确定"保存

### 配置接口字段

1. 进入接口详情页面（从接口列表点击接口名称或"查看"按钮）
2. 在字段列表部分，点击"新增字段"按钮
3. 添加输入参数（请求参数）：
   - 参数编码：startDate
   - 参数名称：开始日期
   - 参数位置：1
   - 参数类型：输入参数
   - 数据类型：日期
   - 是否显示：是
   - 是否导出：否
4. 添加输出字段（响应参数）：
   - 参数编码：order_id
   - 参数名称：订单号
   - 参数位置：1
   - 参数类型：输出参数
   - 数据类型：字符
   - 是否显示：是
   - 是否导出：是
5. 调整字段顺序（修改参数位置数字，系统自动排序）
6. 点击"确定"保存字段

**字段类型说明：**
- **输入参数**：用于查询条件，如日期范围、状态筛选等
- **输出参数**：用于返回结果展示，支持15种数据类型
- **数据类型**：字符、整数、小数、百分比、日期、年份、月份、单选、多选、文本等

### 执行接口查询

1. 进入"数据服务" → "接口管理"
2. 找到需要执行的接口
3. 点击"执行"按钮
4. 输入参数值（如果有输入参数）
5. 查看查询结果
6. （可选）导出为 CSV

### 导入接口元数据

1. 进入"数据服务" → "接口管理"
2. 点击"导入元数据"按钮
3. 下载导入模板
4. 按模板格式填写接口信息
5. 上传填写好的 Excel 文件
6. 系统自动创建/更新接口
7. 查看导入结果

### 查看查询日志

1. 进入"数据服务" → "查询日志"
2. 查看所有查询记录，包括：
   - 查询时间
   - 执行用户
   - 数据源名称
   - 执行状态（成功/失败）
   - 执行耗时（毫秒）
   - 查询类型（SQL查询/接口查询）
   - SQL语句（支持查看详情）
   - 错误信息（如果有）
3. 使用筛选功能：
   - 按用户名筛选
   - 按执行状态筛选（全部/成功/失败）
4. 点击"查询"按钮刷新列表
5. 点击"重置"按钮清空筛选条件
6. 对于长SQL，点击"查看详情"按钮查看完整SQL语句

---

## 路由配置

### 前端路由

数据服务模块的路由配置在 `frontend/src/router/index.js` 中：

#### 主路由（通过菜单动态生成）

```javascript
{
  path: '/data-service',
  component: Layout,
  children: [
    {
      path: 'query',
      component: () => import('@/views/data/service/query/index'),
      name: 'DataServiceQuery',
      meta: { title: 'SQL查询', activeMenu: '/data-service/query' }
    },
    {
      path: 'interface',
      component: () => import('@/views/data/service/interface/index'),
      name: 'DataServiceInterface',
      meta: { title: '接口管理', activeMenu: '/data-service/interface' }
    },
    {
      path: 'report',
      component: () => import('@/views/data/service/report/index'),
      name: 'DataServiceReport',
      meta: { title: '报表管理', activeMenu: '/data-service/report' }
    }
  ]
}
```

#### 动态路由（隐藏路由）

接口详情页面和查询日志页面通过动态路由配置，需要权限才能访问：

```javascript
{
  path: '/data-service',
  component: Layout,
  hidden: true,
  permissions: ['system:dataservice:interface'],
  children: [
    {
      path: 'interface/:interfaceId(\\d+)',
      component: () => import('@/views/data/service/interface/detail'),
      name: 'InterfaceDetail',
      meta: { title: '接口详情', activeMenu: '/data-service/interface' }
    },
    {
      path: 'query-log',
      component: () => import('@/views/data/service/query/queryLog'),
      name: 'DataServiceQueryLog',
      meta: { title: '查询日志', activeMenu: '/data-service/query-log' }
    }
  ]
}
```

**路由说明：**
- **路径格式**: `/data-service/interface/:interfaceId`，其中 `interfaceId` 为数字参数
- **路由名称**: `InterfaceDetail`
- **权限要求**: `system:dataservice:interface`
- **侧边栏高亮**: 访问详情页时高亮 `/data-service/interface` 菜单
- **跳转方式**:
  ```javascript
  // 使用路由名称跳转（推荐）
  router.push({ name: 'InterfaceDetail', params: { interfaceId: id } })

  // 或使用路径跳转
  router.push(`/data-service/interface/${id}`)
  ```

### 后端路由

数据服务模块的路由配置在 `backend/apps/dataservice/urls.py` 中：

```python
router.register(r'query-log', QueryLogViewSet, basename='dataservice-query-log')
router.register(r'interface-info', InterfaceInfoViewSet, basename='dataservice-interface-info')
router.register(r'interface-field', InterfaceFieldViewSet, basename='dataservice-interface-field')

urlpatterns = [
    path('query', QueryServiceView.as_view({'post': 'query'}), name='dataservice-query'),
    path('export', QueryServiceView.as_view({'post': 'export'}), name='dataservice-export'),
    path('', include(router.urls)),
]
```

---

## 权限说明

### 菜单权限标识

| 菜单 | 权限标识 | 说明 |
|------|---------|------|
| SQL 查询 | `system:dataservice:query` | 执行 SQL 查询 |
| 接口管理 | `system:dataservice:interface` | 管理数据接口 |
| 接口新增 | `system:dataservice:add` | 新增接口 |
| 接口修改 | `system:dataservice:edit` | 修改接口 |
| 接口删除 | `system:dataservice:remove` | 删除接口 |
| 查询日志 | `system:dataservice:log` | 查看查询日志 |

**注意：** admin 用户拥有所有权限，其他用户需要分配相应权限。

---

## 关键文件位置

### 后端文件

```
backend/apps/dataservice/
├── __init__.py
├── models.py                # 3个数据模型
├── serializers.py           # 所有序列化器
├── views.py                 # 所有 ViewSet
├── urls.py                  # URL 路由配置
├── custom.py                # Excel 导入导出工具
└── migrations/              # 数据库迁移文件
    ├── 0001_initial.py
    ├── 0002_querylog_query_type.py
    ├── 0003_interfaceinfo_enable.py
    ├── 0004_alter_interfaceinfo_enable.py
    ├── 0005_alter_interfaceinfo_enable.py
    └── 0006_interfaceinfo_module_name_and_more.py
```

### 前端文件

```
frontend/src/
├── api/data/
│   └── service.js              # 统一 API 封装
└── views/data/service/
    ├── index.vue                # 主页
    ├── query/
    │   ├── index.vue            # SQL 查询页面
    │   ├── queryView.vue        # 查询编辑器
    │   ├── queryResult.vue      # 结果展示
    │   ├── queryLog.vue         # 查询日志
    │   └── resizable-splitter.vue
    ├── interface/
    │   ├── index.vue            # 接口管理
    │   └── detail.vue           # 接口详情
    └── report/
        └── index.vue            # 报表管理（规划中）
```

### 配置文件

```
backend/config/
├── settings.py            # 已更新 INSTALLED_APPS
└── urls.py                # 已添加 dataservice 路由
```

---

## 版本历史

### v1.2.0 (2026-02-05)

**新增查询日志菜单：**
- ✅ **查询日志独立菜单**
  - 新增"查询日志"子菜单（order: 3）
  - 路由路径：/data-service/query-log
  - 权限标识：system:dataservice:querylog
- ✅ **前端路由更新**
  - 添加 DataServiceQueryLog 路由
  - 支持权限控制访问
- ✅ **菜单初始化优化**
  - 更新菜单初始化命令（4步骤）
  - 支持查询日志菜单自动创建
- ✅ **文档更新**
  - 更新模块文档，包含查询日志功能说明
  - 添加使用指南和配置说明

**核心改进：**
- ⭐ 查询日志独立入口（方便快速访问）
- ⭐ 完善的权限控制体系
- ⭐ 统一的菜单管理规范

### v1.1.0 (2026-02-05)

**布局优化重大更新：**
- ✅ **智能布局管理系统**
  - 三种预设布局（编辑优先/均衡布局/结果优先）
  - 拖拽分割条自定义高度
  - 布局偏好持久化（localStorage）
- ✅ **响应式高度适配**
  - 设备类型识别（移动/平板/桌面）
  - 窗口大小变化监听（200ms 防抖）
  - 智能比例保持（预设模式/自定义模式）
- ✅ **增强的分割条组件**
  - 视觉反馈（悬停高亮、拖拽动画）
  - Tooltip 提示
  - 首次使用引导提示
- ✅ **改进的用户体验**
  - 移除查询成功后自动调整（不打乱用户布局）
  - 优化初始布局（默认显示分割条）
  - 空状态提示（"执行查询后在此显示结果"）

**核心改进：**
- ⭐ 简化高度计算逻辑（配置驱动）
- ⭐ 移除魔法数字（200、100、8 → 可配置）
- ⭐ 智能默认布局（移动端结果优先）
- ⭐ 平滑过渡动画（0.3s ease）

**技术实现：**
- Vue 3 响应式高度计算
- window resize 事件监听
- 防抖优化（性能提升）
- 设备断点识别（768/1024/1440px）

### v1.0.0 (2025-02-05)

**初始版本：**
- ✅ SQL 查询服务（多数据源、动态参数、分页导出）
- ✅ 数据接口管理（CRUD、字段配置）
- ✅ 接口执行和导出
- ✅ 接口元数据导入导出（Excel）
- ✅ 查询日志审计
- ✅ 完成前后端完整实现

**核心功能：**
- ⭐ 多标签页 SQL 查询编辑器
- ⭐ Django Template 参数化查询
- ⭐ 接口字段自动排序
- ⭐ Excel 批量导入接口定义
- ⭐ 完整的查询审计日志

**技术实现：**
- Django REST Framework
- Vue 3 Composition API
- Element Plus UI 组件
- Django Template SQL 渲染
- openpyxl Excel 处理

---

## 后续扩展计划

### 短期优化
1. 报表服务实现
2. API 网关增强（自动生成、认证、限流）
3. 高级查询功能（语法高亮、智能补全）
4. 查询性能分析（执行计划、慢查询）
5. 查询结果缓存

### 中期规划
1. 数据订阅服务（WebHook、消息队列、CDC）
2. 权限增强（行级安全 RLS、列级安全 CLS）
3. 动态数据脱敏
4. GraphQL 支持
5. 实时数据推送（WebSocket）

### 长期规划
1. 自动化 BI（AI 辅助查询、报表推荐）
2. 预测分析
3. 数据商品化平台
4. 多租户隔离增强
5. 数据服务治理

---

**文档版本**: v1.2.0
**最后更新**: 2026-02-05
**维护者**: Data Admin 开发团队
