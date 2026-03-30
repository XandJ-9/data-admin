# Frontend Development Conventions

## Package Management

Use `pnpm` instead of `npm` or `yarn`:
```bash
pnpm install
pnpm add <package>
pnpm add -D <dev_package>
```

## Directory Structure

```
src/
├── api/              # API wrappers by module
├── views/            # Page components
├── components/       # Reusable components
├── router/           # Vue Router config
├── store/            # Pinia stores
└── utils/            # Request interceptor, auth helpers
```

## API Wrapper Pattern

Create `src/api/module.js`:
```javascript
import request from '@/utils/request'

export function listXxx(query) {
  return request({ url: '/module/', method: 'get', params: query })
}

export function getXxx(id) {
  return request({ url: `/module/${id}/`, method: 'get' })
}

export function addXxx(data) {
  return request({ url: '/module/', method: 'post', data })
}

export function updateXxx(data) {
  return request({ url: `/module/${data.xxxId}/`, method: 'put', data })
}

export function delXxx(id) {
  return request({ url: `/module/${id}/`, method: 'delete' })
}
```

## Component Pattern (CRUD Page)

```vue
<template>
  <!-- Search Form -->
  <el-form :model="queryParams" ref="queryRef" :inline="true">
    <el-form-item label="名称" prop="name">
      <el-input v-model="queryParams.name" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleQuery">搜索</el-button>
      <el-button @click="resetQuery">重置</el-button>
    </el-form-item>
  </el-form>

  <!-- Data Table -->
  <el-table :data="dataList">
    <el-table-column prop="name" label="名称" />
    <el-table-column label="操作" width="180">
      <template #default="{ row }">
        <el-button link type="primary" @click="handleUpdate(row)">修改</el-button>
        <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>

  <!-- Pagination -->
  <pagination
    v-show="total > 0"
    :total="total"
    v-model:page="queryParams.pageNum"
    v-model:limit="queryParams.pageSize"
    @pagination="getList"
  />

  <!-- Edit Dialog -->
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

## Naming Conventions

| Context | Convention | Example |
|---------|------------|---------|
| Component name | `PascalCase` | `TaskDetail.vue` |
| File name | `camelCase` or `kebab-case` | `taskList.vue`, `index.vue` |
| API file | `camelCase` | `datasource.js`, `etl.js` |
| Variables/Functions | `camelCase` | `handleQuery()`, `tableList` |
| Constants | `UPPER_SNAKE_CASE` | `PAGE_SIZE` |

## Common Commands

```bash
cd frontend

# Setup
pnpm install

# Dev
pnpm dev

# Build
pnpm build:prod
pnpm build:stage
```

## Common Components

| Component | Purpose |
|-----------|---------|
| `<pagination>` | Standard pagination with `total`, `page`, `limit` props |
| `<el-dialog>` | Modal dialogs for forms |
| `<right-toolbar>` | Table column visibility toggle |
| `<code-editor>` | Ace Editor for SQL/code editing |
| `<dict-tag>` | Dictionary value display |
| `<image-upload>` | Image upload with preview |

## API Response Format

Backend returns camelCase JSON:
```javascript
// List response
{ code: 200, rows: [...], total: 50 }

// Detail response
{ code: 200, data: { id: 1, taskName: '...', createTime: '...' } }
```

## Important Notes

1. **Dynamic Routes**: Menus generated from backend `GET /getRouters`
2. **Request Interceptor**: Auto-adds JWT token via `Authorization: Bearer <token>`
3. **Error Handling**: 401 redirects to login, 500/601 shows message
4. **Pinia Stores**: Use for global state (user, permission, dict, settings)
