# 前端开发规范

## 技术栈

- **框架**：Vue 3.5 + Vue Router 4.5 + Pinia 3.0
- **UI 组件库**：Element Plus 2.10
- **构建工具**：Vite 6
- **语言**：JavaScript（非 TypeScript）
- **包管理器**：`pnpm`

## 包管理

使用 `pnpm` 代替 `npm` 或 `yarn`：
```bash
pnpm install              # 安装依赖
pnpm add <package>        # 添加运行时依赖
pnpm add -D <dev_package> # 添加开发依赖
```

## 目录结构

```
src/
├── api/              # API 接口封装（按模块分目录）
│   ├── data/         #   数据管理模块（datasource, asset, service, datadev, studio, integration）
│   ├── system/       #   系统管理模块（user, role, dept, menu, config, dict）
│   ├── monitor/      #   监控模块（server, job, operlog, logininfor, online, cache）
│   ├── login.js      #   登录认证
│   └── terminal.js   #   终端管理
├── views/            # 页面组件（按功能模块分目录）
│   ├── data/         #   数据模块（datasource, asset, etl, service）
│   ├── system/       #   系统管理（user, role, dept, menu, dict, config, post, notice）
│   ├── monitor/      #   监控（server, operlog, logininfor, online, cache, job）
│   ├── terminal/     #   Web 终端
│   └── tool/         #   开发工具（swagger, gen, build）
├── components/       # 全局复用组件
├── router/           # 路由配置
├── store/            # Pinia 状态管理
├── utils/            # 工具函数
├── plugins/          # 全局插件（auth, cache, modal, download, tab）
├── directive/        # 自定义指令（v-hasRole, v-hasPermi, v-copyText）
├── layout/           # 布局组件
└── assets/           # 静态资源
```

## API 接口封装模式

在 `src/api/` 下按模块创建文件：
```javascript
import request from '@/utils/request'

// 获取列表
export function listXxx(query) {
  return request({ url: '/module/', method: 'get', params: query })
}

// 获取详情
export function getXxx(id) {
  return request({ url: `/module/${id}/`, method: 'get' })
}

// 新增
export function addXxx(data) {
  return request({ url: '/module/', method: 'post', data })
}

// 修改
export function updateXxx(data) {
  return request({ url: `/module/${data.xxxId}/`, method: 'put', data })
}

// 删除
export function delXxx(id) {
  return request({ url: `/module/${id}/`, method: 'delete' })
}
```

## CRUD 页面组件模式

```vue
<template>
  <!-- 搜索表单 -->
  <el-form :model="queryParams" ref="queryRef" :inline="true">
    <el-form-item label="名称" prop="name">
      <el-input v-model="queryParams.name" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleQuery">搜索</el-button>
      <el-button @click="resetQuery">重置</el-button>
    </el-form-item>
  </el-form>

  <!-- 数据表格 -->
  <el-table :data="dataList">
    <el-table-column prop="name" label="名称" />
    <el-table-column label="操作" width="180">
      <template #default="{ row }">
        <el-button link type="primary" @click="handleUpdate(row)">修改</el-button>
        <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>

  <!-- 分页 -->
  <pagination
    v-show="total > 0"
    :total="total"
    v-model:page="queryParams.pageNum"
    v-model:limit="queryParams.pageSize"
    @pagination="getList"
  />

  <!-- 编辑对话框 -->
  <el-dialog v-model="open" :title="title" width="500px">
    <el-form :model="form" :rules="rules" ref="formRef">
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button type="primary" @click="submitForm">确 定</el-button>
      <el-button @click="cancel">取 消</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { listXxx, getXxx, addXxx, updateXxx, delXxx } from '@/api/module'

const queryParams = ref({ pageNum: 1, pageSize: 10, name: null })
const dataList = ref([])
const total = ref(0)
const open = ref(false)
const title = ref('')
const form = ref({})

function getList() {
  listXxx(queryParams.value).then(res => {
    dataList.value = res.rows
    total.value = res.total
  })
}

function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

function resetQuery() {
  queryParams.value = { pageNum: 1, pageSize: 10, name: null }
  getList()
}

function handleAdd() {
  form.value = {}
  open.value = true
  title.value = '添加'
}

function handleUpdate(row) {
  getXxx(row.id).then(res => {
    form.value = res.data
    open.value = true
    title.value = '修改'
  })
}

function submitForm() {
  const apiCall = form.value.id ? updateXxx : addXxx
  apiCall(form.value).then(() => {
    useMessage().success('操作成功')
    open.value = false
    getList()
  })
}

function handleDelete(row) {
  useMessage().confirm('确认删除?').then(() => {
    delXxx(row.id).then(() => {
      useMessage().success('删除成功')
      getList()
    })
  })
}

getList()
</script>
```

## 命名规范

| 场景 | 命名风格 | 示例 |
|------|----------|------|
| 组件名 | `PascalCase` | `TaskDetail.vue` |
| 文件名 | `camelCase` 或 `kebab-case` | `taskList.vue`, `index.vue` |
| API 文件 | `camelCase` | `datasource.js`, `etl.js` |
| 变量/函数 | `camelCase` | `handleQuery()`, `tableList` |
| 常量 | `UPPER_SNAKE_CASE` | `PAGE_SIZE` |

## 状态管理（Pinia）

| Store 模块 | 说明 | 关键状态 |
|------------|------|----------|
| `user` | 用户认证 | `token`, `name`, `nickName`, `avatar`, `roles`, `permissions` |
| `permission` | 动态路由 | `routes`, `addRoutes`, `sidebarRouters`, `topbarRouters` |
| `app` | 应用状态 | `sidebar`（展开/折叠）, `device`（桌面/移动端）, `size` |
| `settings` | 界面设置 | `theme`, `sideTheme`, `topNav`, `tagsView`, `fixedHeader`, `isDark` |
| `tagsView` | 标签页 | `visitedViews`, `cachedViews`, `iframeViews` |
| `dict` | 字典缓存 | `dict`（键值对数组） |

## 全局复用组件

| 组件 | 用途 |
|------|------|
| `<pagination>` | 标准分页，props: `total`, `page`, `limit` |
| `<right-toolbar>` | 表格列显隐切换工具栏 |
| `<code-editor>` | Ace Editor 代码编辑器（SQL/代码） |
| `<dict-tag>` | 字典值标签显示 |
| `<image-upload>` | 图片上传与预览 |
| `<file-upload>` | 文件上传 |
| `<image-preview>` | 图片预览弹窗 |
| `<editor>` | 富文本编辑器（Quill） |
| `<field-mapping>` | 字段映射界面 |
| `<svg-icon>` | SVG 图标组件 |
| `<select-form>` | 动态表单字段 |
| `<el-dialog>` | 弹窗对话框（Element Plus） |

## 自定义指令

| 指令 | 用途 | 示例 |
|------|------|------|
| `v-hasRole` | 角色权限显隐 | `v-hasRole="['admin']"` |
| `v-hasPermi` | 按钮权限显隐 | `v-hasPermi="['system:user:add']"` |
| `v-copyText` | 点击复制文本 | `v-copyText="textValue"` |

## 全局插件

| 插件 | 全局属性 | 提供方法 |
|------|----------|----------|
| `auth` | `$auth` | `hasPermi()`, `hasRole()`, `hasPermiOr()`, `hasRoleOr()` |
| `cache` | `$cache` | Session/Local 存储，支持 JSON |
| `modal` | `$modal` | 消息提示、确认对话框、通知 |
| `download` | `$download` | 文件/Excel 下载工具 |
| `tab` | `$tab` | 标签页操作 |

## 工具函数

| 文件 | 说明 |
|------|------|
| `utils/request.js` | Axios 实例，请求/响应拦截器，`download()` |
| `utils/auth.js` | `getToken()`, `setToken()`, `removeToken()` |
| `utils/validate.js` | 表单验证：`isEmpty()`, `isHttp()`, `validEmail()`, `validURL()` |
| `utils/ruoyi.js` | 通用工具：`parseTime()`, `addDateRange()`, `selectDictLabel()` |
| `utils/permission.js` | 权限校验：`checkPermi()`, `checkRole()` |
| `utils/dict.js` | 字典组合式函数：`useDict()` |
| `utils/terminalWs.js` | WebSocket 连接管理（自动重连、心跳检测） |
| `utils/jsencrypt.js` | RSA 加密工具 |

## 路由系统

- **静态路由**：登录、404/401 错误页、用户中心、Web 终端
- **动态路由**：通过后端 `GET /getRouters` 接口返回，由 `permission` store 动态注册
- **路由守卫**：`src/permission.js` 实现全局前置守卫，处理 Token 校验和路由生成
- **白名单**：当前仅 `/login` 无需认证

## 请求拦截器

- **请求拦截**：自动添加 `Authorization: Bearer <token>` 头部，防重复提交
- **响应拦截**：处理 401（重新登录）、500/601（错误提示）、二进制 Blob 下载
- **下载方法**：支持 Blob 响应，自动提取文件名

## API 响应格式

后端返回 camelCase JSON：
```javascript
// 列表响应
{ code: 200, rows: [...], total: 50 }

// 详情响应
{ code: 200, data: { id: 1, taskName: '...', createTime: '...' } }

// 操作成功
{ code: 200, msg: '操作成功' }
```

## 常用命令

```bash
cd frontend

# 安装依赖
pnpm install

# 开发模式（端口 80）
pnpm dev

# 生产构建
pnpm build:prod

# 预发布构建
pnpm build:stage
```

## 重要注意事项

1. **动态路由**：菜单由后端 `GET /getRouters` 接口动态生成，无需手动配置路由文件
2. **请求拦截器**：自动通过 `Authorization: Bearer <token>` 携带 JWT 令牌
3. **错误处理**：401 自动跳转登录页，500/601 显示错误消息
4. **Pinia Store**：用于全局状态管理（用户、权限、字典、设置）
5. **Element Plus**：使用中文语言包（`zhCn`）
6. **主题切换**：支持亮色/暗色主题切换
7. **移动端适配**：992px 以下自动切换为移动端布局
8. **使用 JavaScript**：本项目使用 JavaScript，不要建议迁移至 TypeScript
