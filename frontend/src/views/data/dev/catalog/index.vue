<template>
  <div class="app-container">
    <el-form v-show="showSearch" ref="queryRef" :inline="true" :model="queryParams">
      <el-form-item label="目录名称" prop="directoryName">
        <el-input
          v-model="queryParams.directoryName"
          placeholder="请输入目录名称"
          clearable
          style="width: 220px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="目录编码" prop="directoryCode">
        <el-input
          v-model="queryParams.directoryCode"
          placeholder="请输入目录编码"
          clearable
          style="width: 220px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="请选择状态" clearable style="width: 180px">
          <el-option
            v-for="dict in sys_normal_disable"
            :key="dict.value"
            :label="dict.label"
            :value="dict.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="Plus"
          v-hasPermi="['datadev:catalog:add']"
          @click="handleAdd"
        >新增目录</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="info" plain icon="Sort" @click="collapseAllDirectories">全部收起</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList" />
    </el-row>

    <div v-loading="loading" class="directory-collapse-wrap">
      <el-collapse v-model="activeCollapseName" accordion class="directory-collapse" @change="handleCollapseChange">
        <el-collapse-item
          v-for="directory in directoryCards"
          :key="directory.directoryId"
          :name="String(directory.directoryId)"
          class="directory-collapse-item"
        >
          <template #title>
            <div class="directory-card-header" :style="{ paddingLeft: `${directory.depth * 20}px` }">
              <div class="directory-card-main">
                <div class="directory-card-title-row">
                  <span class="directory-card-title">{{ directory.directoryName }}</span>
                  <el-tag size="small" effect="plain">{{ directory.directoryCode }}</el-tag>
                  <dict-tag :options="sys_normal_disable" :value="directory.status" />
                </div>
                <div class="directory-card-summary">
                <span>当前目录：{{ directory.directoryName }}</span>
                <el-tag size="small" effect="plain">共 {{ getDirectoryScripts(directory.directoryId).length }} 个脚本</el-tag>
                </div>
                <div class="directory-card-meta">
                  <span>排序 {{ directory.orderNum }}</span>
                  <span>更新时间 {{ directory.updateTime || '-' }}</span>
                </div>
              </div>
              <div class="directory-card-actions" @click.stop>
                <el-button
                  link
                  type="primary"
                  icon="Edit"
                  v-hasPermi="['datadev:catalog:edit']"
                  @click="handleUpdate(directory)"
                >
                  修改
                </el-button>
                <el-button
                  link
                  type="danger"
                  icon="Delete"
                  v-hasPermi="['datadev:catalog:remove']"
                  @click="handleDelete(directory)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </template>

          <div class="directory-card-body">
            <div v-loading="isDirectoryLoading(directory.directoryId)" class="directory-script-panel">
              <el-scrollbar height="240px">
                <el-table :data="getDirectoryScripts(directory.directoryId)" size="small" border>
                  <el-table-column prop="scriptName" label="脚本名称" min-width="220" show-overflow-tooltip>
                    <template #default="scope">
                      <el-link type="primary" :underline="false" @click="openScriptInIde(scope.row)">
                        {{ scope.row.scriptName }}
                      </el-link>
                    </template>
                  </el-table-column>
                  <el-table-column prop="scriptCode" label="脚本编码" min-width="160" show-overflow-tooltip />
                  <el-table-column prop="directoryName" label="所属目录" min-width="140" show-overflow-tooltip />
                  <el-table-column prop="scriptType" label="类型" width="90" />
                  <el-table-column prop="status" label="状态" width="100">
                    <template #default="scope">
                      <el-tag size="small" :type="scope.row.status === 'published' ? 'success' : 'info'" effect="plain">
                        {{ scope.row.status === 'published' ? '已发布' : '草稿' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="updateTime" label="更新时间" width="180" />
                </el-table>
                <div
                  v-if="!isDirectoryLoading(directory.directoryId) && getDirectoryScripts(directory.directoryId).length === 0"
                  class="script-empty"
                >
                  当前目录下暂无脚本
                </div>
              </el-scrollbar>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
      <el-empty v-if="directoryCards.length === 0 && !loading" description="暂无数据目录" />
    </div>

    <el-dialog v-model="open" :title="title" width="640px" append-to-body>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row>
          <el-col :span="24">
            <el-form-item label="上级目录" prop="parentId">
              <el-tree-select
                v-model="form.parentId"
                :data="directoryOptions"
                :props="{ value: 'directoryId', label: 'directoryName', children: 'children' }"
                value-key="directoryId"
                placeholder="请选择上级目录"
                check-strictly
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目录名称" prop="directoryName">
              <el-input v-model="form.directoryName" placeholder="请输入目录名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目录编码" prop="directoryCode">
              <el-input v-model="form.directoryCode" placeholder="请输入目录编码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序" prop="orderNum">
              <el-input-number v-model="form.orderNum" :min="0" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-radio-group v-model="form.status">
                <el-radio
                  v-for="dict in sys_normal_disable"
                  :key="dict.value"
                  :value="dict.value"
                >
                  {{ dict.label }}
                </el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button type="primary" :loading="submitting" @click="submitForm">确 定</el-button>
        <el-button @click="cancel">取 消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listDirectories,
  addDirectory,
  updateDirectory,
  delDirectory,
  getDirectoryTree,
  listScripts,
} from '@/api/data/datadev'

defineOptions({ name: 'DataDevCatalog' })

const { proxy } = getCurrentInstance()
const { sys_normal_disable } = proxy.useDict('sys_normal_disable')
const router = useRouter()

const loading = ref(false)
const showSearch = ref(true)
const activeCollapseName = ref('')
const open = ref(false)
const title = ref('')
const submitting = ref(false)

const directoryList = ref([])
const directoryTree = ref([])
const directoryOptions = ref([])
const directoryScriptMap = ref({})
const directoryLoadingMap = ref({})

const queryParams = reactive({
  directoryName: '',
  directoryCode: '',
  status: '',
})

const form = reactive({
  directoryId: undefined,
  parentId: 0,
  directoryName: '',
  directoryCode: '',
  orderNum: 0,
  status: '0',
  remark: '',
})

const rules = {
  parentId: [{ required: true, message: '请选择上级目录', trigger: 'change' }],
  directoryName: [{ required: true, message: '请输入目录名称', trigger: 'blur' }],
  directoryCode: [{ required: true, message: '请输入目录编码', trigger: 'blur' }],
  orderNum: [{ required: true, message: '请输入排序', trigger: 'blur' }],
}

function resetForm() {
  form.directoryId = undefined
  form.parentId = 0
  form.directoryName = ''
  form.directoryCode = ''
  form.orderNum = 0
  form.status = '0'
  form.remark = ''
  proxy.resetForm('formRef')
}

function buildTree(items, parentId = 0) {
  return items
    .filter((item) => Number(item.parentId) === Number(parentId))
    .map((item) => {
      const children = buildTree(items, item.directoryId)
      if (children.length > 0) {
        return { ...item, children }
      }
      return { ...item }
    })
}

function buildDirectoryCards(nodes, depth = 0) {
  return (nodes || []).flatMap((node) => {
    const currentNode = { ...node, depth }
    const children = buildDirectoryCards(node.children || [], depth + 1)
    return [currentNode, ...children]
  })
}

const directoryCards = computed(() => buildDirectoryCards(directoryTree.value))

function buildTreeOptions(items, excludeId) {
  let filtered = items
  if (excludeId) {
    const excludedIds = new Set([Number(excludeId)])
    const collectDescendants = (parentId) => {
      items.forEach((item) => {
        if (Number(item.parentId) === Number(parentId)) {
          excludedIds.add(Number(item.directoryId))
          collectDescendants(item.directoryId)
        }
      })
    }
    collectDescendants(excludeId)
    filtered = items.filter((item) => !excludedIds.has(Number(item.directoryId)))
  }
  const rootNode = { directoryId: 0, directoryName: '根目录', children: [] }
  rootNode.children = buildTree(filtered, 0)
  return [rootNode]
}

async function getList() {
  loading.value = true
  try {
    const res = await listDirectories(queryParams)
    directoryList.value = res.data || []
    directoryTree.value = buildTree(directoryList.value, 0)
    directoryOptions.value = buildTreeOptions(directoryList.value)
    Object.keys(directoryScriptMap.value).forEach((directoryId) => {
      const exists = directoryList.value.some((item) => Number(item.directoryId) === Number(directoryId))
      if (!exists) {
        delete directoryScriptMap.value[directoryId]
        delete directoryLoadingMap.value[directoryId]
      }
    })
    if (activeCollapseName.value) {
      const exists = directoryCards.value.some((item) => String(item.directoryId) === activeCollapseName.value)
      if (exists) {
        handleCollapseChange(activeCollapseName.value)
      } else {
        activeCollapseName.value = ''
      }
    }
  } catch (error) {
    directoryList.value = []
    directoryTree.value = []
    directoryOptions.value = [{ directoryId: 0, directoryName: '根目录', children: [] }]
    activeCollapseName.value = ''
  } finally {
    loading.value = false
  }
}

function collectDescendantDirectoryIds(parentId) {
  const result = []
  const loop = (currentParentId) => {
    directoryList.value.forEach((item) => {
      if (Number(item.parentId) === Number(currentParentId)) {
        result.push(item.directoryId)
        loop(item.directoryId)
      }
    })
  }
  loop(parentId)
  return result
}

async function fetchScriptsByDirectoryId(directoryId) {
  const pageSize = 100
  let pageNum = 1
  let mergedRows = []

  while (true) {
    const res = await listScripts({ directoryId, pageNum, pageSize })
    const rows = res.rows || res.data || []
    mergedRows = mergedRows.concat(rows)
    if (rows.length < pageSize) {
      break
    }
    pageNum += 1
  }

  return mergedRows
}

async function loadDirectoryScripts(directoryId) {
  if (!directoryId || directoryScriptMap.value[directoryId]) return
  directoryLoadingMap.value[directoryId] = true
  try {
    const directoryIds = [directoryId, ...collectDescendantDirectoryIds(directoryId)]
    const scriptRows = await Promise.all(directoryIds.map((directoryId) => fetchScriptsByDirectoryId(directoryId)))
    const scriptMap = new Map()
    scriptRows.flat().forEach((script) => {
      scriptMap.set(script.scriptId, script)
    })
    directoryScriptMap.value[directoryId] = Array.from(scriptMap.values())
  } catch {
    directoryScriptMap.value[directoryId] = []
    ElMessage.error('加载目录脚本失败')
  } finally {
    directoryLoadingMap.value[directoryId] = false
  }
}

function getDirectoryScripts(directoryId) {
  return directoryScriptMap.value[directoryId] || []
}

function isDirectoryLoading(directoryId) {
  return Boolean(directoryLoadingMap.value[directoryId])
}

function handleCollapseChange(activeNames) {
  const names = Array.isArray(activeNames) ? activeNames : [activeNames].filter(Boolean)
  names.forEach((name) => {
    const directoryId = Number(name)
    if (directoryId) {
      loadDirectoryScripts(directoryId)
    }
  })
}

function collapseAllDirectories() {
  activeCollapseName.value = ''
}

function openScriptInIde(script) {
  if (!script?.scriptId) return
  router.push({
    path: '/datadev/ide',
    query: { scriptId: String(script.scriptId) },
  })
}

async function loadTreeOptions(excludeId) {
  try {
    const res = await getDirectoryTree()
    const treeNodes = res.data || []
    const flatNodes = flattenTree(treeNodes)
    directoryOptions.value = buildTreeOptions(flatNodes, excludeId)
  } catch {
    directoryOptions.value = [{ directoryId: 0, directoryName: '根目录', children: [] }]
  }
}

function flattenTree(treeNodes) {
  const rows = []
  const loop = (nodes) => {
    ;(nodes || []).forEach((node) => {
      rows.push({
        directoryId: node.directoryId,
        parentId: node.parentId,
        directoryName: node.directoryName,
        directoryCode: node.directoryCode,
        orderNum: node.orderNum,
        status: node.status,
        remark: node.remark,
      })
      if (node.children?.length) {
        loop(node.children)
      }
    })
  }
  loop(treeNodes)
  return rows
}

function handleQuery() {
  getList()
}

function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
}

async function handleUpdate(row) {
  resetForm()
  await loadTreeOptions(row.directoryId)
  form.directoryId = row.directoryId
  form.parentId = row.parentId
  form.directoryName = row.directoryName
  form.directoryCode = row.directoryCode
  form.orderNum = row.orderNum
  form.status = row.status
  form.remark = row.remark || ''
  title.value = '修改数据目录'
  open.value = true
}

async function handleAdd() {
  resetForm()
  await loadTreeOptions()
  title.value = '新增数据目录'
  open.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`是否确认删除目录“${row.directoryName}”？`, '删除提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await delDirectory(row.directoryId)
    ElMessage.success('删除成功')
    await getList()
  } catch {
    ElMessage.error('删除失败')
  }
}

function cancel() {
  open.value = false
  resetForm()
}

async function submitForm() {
  try {
    await proxy.$refs.formRef.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const payload = {
      parentId: form.parentId,
      directoryName: form.directoryName,
      directoryCode: form.directoryCode,
      orderNum: form.orderNum,
      status: form.status,
      remark: form.remark,
    }

    if (form.directoryId) {
      await updateDirectory(form.directoryId, payload)
      ElMessage.success('修改成功')
    } else {
      await addDirectory(payload)
      ElMessage.success('新增成功')
    }
    open.value = false
    await getList()
  } catch {
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  getList()
})
</script>

<style lang="scss" scoped>
.directory-collapse-wrap {
  margin-top: 12px;
}

.directory-collapse {
  border-top: none;
}

.directory-collapse-item {
  margin-bottom: 12px;
  border: 1px solid #dbe5ef;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);

  :deep(.el-collapse-item__header) {
    min-height: 84px;
    padding: 0 18px;
    border-bottom: none;
    line-height: normal;
    background: linear-gradient(180deg, #fbfdff 0%, #f7fafc 100%);
  }

  :deep(.el-collapse-item__wrap) {
    border-bottom: none;
  }

  :deep(.el-collapse-item__content) {
    padding-bottom: 0;
  }
}

.directory-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 16px;
}

.directory-card-main {
  flex: 1;
  min-width: 0;
}

.directory-card-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.directory-card-title {
  font-size: 15px;
  font-weight: 700;
  color: #1f2d3d;
}

.directory-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
}

.directory-card-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.directory-card-body {
  padding: 0 18px 18px;
}

.directory-card-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
  color: #4b5563;
}

.directory-script-panel {
  border: 1px solid #e5edf5;
  border-radius: 10px;
  background: #fcfdff;
  padding: 10px;
}

.script-empty {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 16px 0;
}

@media (max-width: 768px) {
  .directory-card-header {
    flex-direction: column;
    align-items: flex-start;
    padding-top: 14px;
    padding-bottom: 14px;
  }

  .directory-card-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .directory-card-summary {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
