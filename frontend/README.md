# 前端（Vue3 + Element Plus）

## 概述

前端基于 [RuoYi-Vue3](https://gitee.com/y_project/RuoYi-Vue) 适配，技术栈为 Vue 3.5 + Element Plus 2.10 + Vite 6 + Pinia + Vue Router 4，配合 Django + DRF 后端实现数据管理平台的全部页面功能。

## 运行与开发

```bash
# 安装 pnpm（如果尚未安装）
npm install -g pnpm

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产环境
pnpm build:prod

# 构建测试环境
pnpm build:stage
```

- Node.js 18+
- 开发地址：`http://localhost:80`（Vite 代理 `/dev-api` → 后端 `http://localhost:8000`）

## 目录结构

```
frontend/src/
├── api/                           # API 封装
│   ├── data/                      #   数据模块 API
│   │   ├── datasource.js          #     数据源管理
│   │   ├── asset.js               #     数据资产（元数据、血缘）
│   │   ├── meta.js                #     元数据查询
│   │   ├── service.js             #     数据服务（查询、接口）
│   │   ├── etl.js                 #     ETL 任务管理
│   │   ├── integration.js         #     数据集成（预留）
│   │   ├── studio.js              #     数据工坊（预留）
│   │   └── taskmonitor.js         #     任务监控（预留）
│   ├── system/                    #   系统管理 API
│   │   ├── user.js                #     用户管理
│   │   ├── role.js                #     角色管理
│   │   ├── menu.js                #     菜单管理
│   │   ├── dept.js                #     部门管理
│   │   ├── post.js                #     岗位管理
│   │   ├── dict/                  #     字典管理
│   │   ├── config.js              #     参数配置
│   │   └── notice.js              #     通知公告
│   ├── monitor/                   #   监控管理 API
│   │   ├── server.js              #     服务监控
│   │   ├── online.js              #     在线用户
│   │   ├── operlog.js             #     操作日志
│   │   ├── logininfor.js          #     登录日志
│   │   ├── job.js                 #     定时任务
│   │   ├── jobLog.js              #     任务日志
│   │   └── cache.js               #     缓存监控
│   ├── login.js                   #   登录/登出
│   └── menu.js                    #   动态路由
├── views/                         # 页面视图
│   ├── data/                      #   数据模块页面
│   │   ├── datasource/            #     数据源管理
│   │   ├── asset/                 #     数据资产
│   │   │   ├── index.vue          #       仪表盘总览
│   │   │   ├── metadata/          #       元数据浏览
│   │   │   └── lineage/           #       表血缘可视化
│   │   ├── service/               #     数据服务
│   │   │   ├── index.vue          #       服务总览
│   │   │   ├── query/             #       SQL 在线查询
│   │   │   ├── interface/         #       接口管理
│   │   │   └── report/            #       报表（预留）
│   │   ├── etl/                   #     ETL 管理
│   │   │   ├── index.vue          #       ETL 总览
│   │   │   ├── taskList.vue       #       任务列表
│   │   │   ├── taskDetail.vue     #       任务编辑（SQL/字段映射/版本）
│   │   │   ├── executionLogs.vue  #       执行日志
│   │   │   └── components/        #       ETL 子组件
│   │   └── integration/           #     数据集成（预留）
│   ├── system/                    #   系统管理页面
│   ├── monitor/                   #   监控管理页面
│   ├── login.vue                  #   登录页
│   └── error/                     #   错误页（401/404）
├── store/                         # Pinia 状态管理
│   └── modules/
│       ├── user.js                #   用户状态
│       ├── permission.js          #   权限与动态路由
│       ├── dict.js                #   字典缓存
│       ├── app.js                 #   应用设置
│       ├── settings.js            #   界面设置
│       └── tagsView.js            #   标签页
├── router/                        # 路由
│   └── index.js                   #   静态路由 + 后端动态菜单
├── components/                    # 通用组件
│   ├── Pagination/                #   分页组件
│   ├── CodeEditor/                #   代码编辑器（Ace Editor）
│   ├── FieldMapping/              #   字段映射组件
│   ├── DictTag/                   #   字典标签
│   ├── Editor/                    #   富文本编辑器
│   ├── FileUpload/                #   文件上传
│   ├── ImageUpload/               #   图片上传
│   ├── IconSelect/                #   图标选择
│   ├── RightToolbar/              #   表格右侧工具栏
│   ├── SelectForm/                #   选择表单
│   └── ...                        #   其他 RuoYi 通用组件
├── layout/                        # 布局组件（侧边栏/头部/标签栏）
├── plugins/                       # Vue 插件（Element Plus 等）
├── directive/                     # 自定义指令
├── utils/                         # 工具函数
└── assets/                        # 静态资源
```

## 核心设计

### 技术选型

| 组件 | 说明 |
|------|------|
| Vue 3 Composition API | 现代化组件开发方式 |
| Element Plus | UI 组件库 |
| Pinia | 状态管理（替代 Vuex） |
| Ace Editor | SQL 在线编辑器 |
| ECharts | 图表可视化 |
| 动态路由 | 后端 `GET /getRouters` 接口生成前端菜单与路由 |
| RuoYi 组件适配 | Pagination、Dialog、Table、RightToolbar 等统一交互模式 |

### API 封装模式

所有模块在 `src/api/` 下创建独立文件，统一使用 `request` 工具函数：

```javascript
import request from '@/utils/request'

// 列表查询
export function listXxx(query) {
  return request({ url: '/module/', method: 'get', params: query })
}

// 详情
export function getXxx(id) {
  return request({ url: `/module/${id}/`, method: 'get' })
}

// 创建
export function addXxx(data) {
  return request({ url: '/module/', method: 'post', data })
}

// 更新
export function updateXxx(id, data) {
  return request({ url: `/module/${id}/`, method: 'put', data })
}

// 删除
export function delXxx(id) {
  return request({ url: `/module/${id}/`, method: 'delete' })
}
```

### 页面组件模式

标准 CRUD 页面结构：

```vue
<template>
  <!-- 搜索表单 -->
  <el-form :model="queryParams" ref="queryRef" :inline="true">
    <el-form-item><el-input v-model="queryParams.name" /></el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleQuery">搜索</el-button>
      <el-button @click="resetQuery">重置</el-button>
    </el-form-item>
  </el-form>

  <!-- 数据表格 -->
  <el-table :data="tableList">
    <el-table-column prop="name" label="名称" />
    <el-table-column label="操作">
      <template #default="{ row }">
        <el-button link @click="handleUpdate(row)">修改</el-button>
        <el-button link @click="handleDelete(row)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>

  <!-- 分页 -->
  <pagination v-show="total > 0" :total="total"
    v-model:page="queryParams.pageNum"
    v-model:limit="queryParams.pageSize"
    @pagination="getList" />

  <!-- 编辑弹窗 -->
  <el-dialog v-model="open" :title="title">
    <el-form :model="form" :rules="rules" ref="formRef">
      <!-- 表单字段 -->
    </el-form>
    <template #footer>
      <el-button type="primary" @click="submitForm">确 定</el-button>
      <el-button @click="cancel">取 消</el-button>
    </template>
  </el-dialog>
</template>
```

## 开发规范

### 命名规范

| 场景 | 规范 | 示例 |
|------|------|------|
| 组件名 | `PascalCase` | `TaskDetail.vue` |
| 文件名 | `camelCase` 或 `kebab-case` | `taskList.vue`, `index.vue` |
| API 文件 | `camelCase` | `datasource.js`, `etl.js` |
| 变量/函数 | `camelCase` | `handleQuery()`, `tableList` |
| 常量 | `UPPER_SNAKE_CASE` | `PAGE_SIZE` |

### API 响应约定

后端返回 camelCase JSON，前端直接使用：

```javascript
// 列表响应
{ code: 200, rows: [...], total: 50 }

// 详情响应
{ code: 200, data: { id: 1, taskName: '...', createTime: '...' } }
```

### 新页面开发清单

- [ ] 在 `src/api/` 创建 API 封装文件
- [ ] 在 `src/views/` 创建页面组件
- [ ] 后端配置菜单（通过系统管理 → 菜单管理添加），前端自动生成路由
- [ ] 使用 `<pagination>` 组件处理分页
- [ ] 使用 `<el-dialog>` + `<el-form>` 处理 CRUD 弹窗
- [ ] 使用 `<right-toolbar>` 处理表格列显隐控制

## 构建与部署

```bash
# 构建生产版本
pnpm build:prod

# 输出目录：dist/
# 复制到后端静态目录：
cp -r dist/* ../backend/dist/
```

构建产物由 Django 的 `TemplateView` 在 `/data-admin/` 路径提供服务。
