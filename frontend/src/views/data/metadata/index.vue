<template>
  <div class="app-container">
    <el-radio-group v-model="viewMode" style="margin-bottom: 16px" @change="handleViewModeChange">
      <el-radio-button label="table">表查找</el-radio-button>
      <el-radio-button label="column">字段查找</el-radio-button>
    </el-radio-group>

    <!-- 表查找模式 -->
    <template v-if="viewMode === 'table'">
      <el-form :inline="true" style="margin-bottom: 12px">
        <el-form-item label="表名">
          <el-input v-model="filterName" placeholder="支持模糊匹配" style="width: 220px" />
        </el-form-item>
        <el-form-item label="数据库">
          <el-input v-model="filterDbName" placeholder="支持模糊匹配" style="width: 220px" />
        </el-form-item>
        <el-form-item label="数据源">
          <el-input v-model="filterDataSourceName" placeholder="支持模糊匹配" style="width: 220px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="queryTables">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="displayTables" row-key="id" style="width: 100%; margin-top: 12px" border show-overflow-tooltip>
        <el-table-column prop="tableName" label="表名" />
        <el-table-column prop="comment" label="表描述">
          <template #default="scope">
            <div class="prewrap">{{ scope.row.comment }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="dataSourceName" label="数据源" />
        <el-table-column prop="databaseName" label="数据库" />
        <el-table-column prop="createTime" label="创建同步时间" />
        <el-table-column prop="updateTime" label="修改同步时间" />
        <el-table-column prop="createBy" label="采集人" />
        <el-table-column prop="updateBy" label="更新者" />
        <!-- <el-table-column label="操作" width="260">
          <template #default="scope">
            <el-button size="small" @click="openColumns(scope.row)">查看列</el-button>
            <el-button size="small" type="primary" @click="openEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column> -->
      </el-table>
    </template>

    <!-- 字段查找模式 -->
    <template v-else>
      <el-form :inline="true" style="margin-bottom: 12px">
        <el-form-item label="字段名">
          <el-input v-model="columnFilter.columnName" placeholder="支持模糊匹配" style="width: 220px" clearable />
        </el-form-item>
        <el-form-item label="字段描述">
          <el-input v-model="columnFilter.columnComment" placeholder="支持模糊匹配" style="width: 220px" clearable />
        </el-form-item>
        <el-form-item label="表名">
          <el-input v-model="columnFilter.tableName" placeholder="支持模糊匹配" style="width: 220px" clearable />
        </el-form-item>
        <el-form-item label="数据源">
          <el-input v-model="columnFilter.dataSourceName" placeholder="支持模糊匹配" style="width: 220px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="queryColumns">查询</el-button>
          <el-button @click="resetColumnFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="columnLoading" :data="displayColumns" row-key="uniqueKey" style="width: 100%; margin-top: 12px" border show-overflow-tooltip>
        <el-table-column prop="tableName" label="表名" width="180">
          <template #default="scope">
            <el-link type="primary" @click="goToTable(scope.row)">{{ scope.row.tableName }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="columnName" label="字段名" width="180" />
        <el-table-column prop="columnComment" label="字段描述" width="200">
          <template #default="scope">
            <div class="prewrap">{{ scope.row.columnComment }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="dataType" label="数据类型" width="120" />
        <el-table-column prop="dataSourceName" label="数据源" width="180" />
        <el-table-column prop="databaseName" label="数据库" width="150" />
        <el-table-column prop="isPrimary" label="主键" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.isPrimary ? 'success' : 'info'" size="small">{{ scope.row.isPrimary ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isNullable" label="可空" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.isNullable ? 'info' : 'warning'" size="small">{{ scope.row.isNullable ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="defaultValue" label="默认值" width="120" />
        <el-table-column prop="columnIndex" label="序号" width="70" align="center" />
      </el-table>
    </template>

    <div style="display: flex; justify-content: flex-end; margin-top: 12px">
      <el-pagination
        :current-page="viewMode === 'table' ? pageNum : columnPageNum"
        :page-size="viewMode === 'table' ? pageSize : columnPageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="viewMode === 'table' ? total : columnTotal"
        @size-change="viewMode === 'table' ? handleSizeChange : handleColumnSizeChange"
        @current-change="viewMode === 'table' ? handleCurrentChange : handleColumnCurrentChange"
      />
    </div>

    <!-- 字段弹窗保留，用于表查找模式 -->
    <el-dialog v-model="showColumns" title="字段信息" width="70%">
      <div style="margin-bottom: 8px">当前表：{{ currentTable }}</div>
      <el-table :data="columns" border height="50vh">
        <el-table-column prop="columnIndex" label="序号" width="60" />
        <el-table-column prop="columnName" label="列名" />
        <el-table-column prop="columnComment" label="列描述">
          <template #default="scope"><div class="prewrap">{{ scope.row.columnComment }}</div></template>
        </el-table-column>
        <el-table-column prop="dataType" label="类型" />
        <el-table-column prop="isNullable" label="非空" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.isNullable ? 'warning' : 'info'">{{ scope.row.isNullable ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isPrimary" label="主键" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.isPrimary ? 'success' : 'info'">{{ scope.row.isPrimary ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="defaultValue" label="默认值" />
      </el-table>
      <template #footer>
        <el-button @click="showColumns=false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showForm" :title="formMode==='add' ? '新增源数据表' : '编辑源数据表'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="数据源" prop="dataSourceId">
          <el-select v-model="form.dataSourceId" placeholder="选择数据源" style="width: 320px">
            <el-option v-for="ds in dsOptions" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
          </el-select>
        </el-form-item>
        <el-form-item label="表名" prop="tableName">
          <el-input v-model="form.tableName" placeholder="例如：users" />
        </el-form-item>
        <el-form-item label="表描述" prop="comment">
          <el-input v-model="form.comment" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
        <el-form-item label="数据库" prop="databaseName">
          <el-input v-model="form.databaseName" placeholder="可选，例如：public 或 db01" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm=false">取消</el-button>
        <el-button type="primary" @click="submitForm">提交</el-button>
      </template>
    </el-dialog>
  </div>
 </template>

 <script setup name="DataMeta">
import { listMetaTables, listMetaColumns, addMetaTable, updateMetaTable, delMetaTable, listAllMetaColumns } from '@/api/datameta'
import { listDatasource } from '@/api/datasource'
const { proxy } = getCurrentInstance()

// 视图模式：table-表查找, column-字段查找
const viewMode = ref('table')

// 表查找相关
const tables = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(10)
const filterName = ref('')
const filterDataSourceName = ref('')
const filterDbName = ref('')
const createRange = ref([])
const updateRange = ref([])
const displayTables = computed(() => tables.value)
const loading = ref(false)

// 字段查找相关
const allColumns = ref([])
const columnTotal = ref(0)
const columnPageNum = ref(1)
const columnPageSize = ref(10)
const columnFilter = ref({
  columnName: '',
  columnComment: '',
  tableName: '',
  dataSourceName: ''
})
const columnLoading = ref(false)
const displayColumns = computed(() => {
  let data = allColumns.value
  // 前端过滤
  if (columnFilter.value.columnName) {
    data = data.filter(col => col.columnName?.toLowerCase().includes(columnFilter.value.columnName.toLowerCase()))
  }
  if (columnFilter.value.columnComment) {
    data = data.filter(col => col.columnComment?.toLowerCase().includes(columnFilter.value.columnComment.toLowerCase()))
  }
  if (columnFilter.value.tableName) {
    data = data.filter(col => col.tableName?.toLowerCase().includes(columnFilter.value.tableName.toLowerCase()))
  }
  if (columnFilter.value.dataSourceName) {
    data = data.filter(col => col.dataSourceName?.toLowerCase().includes(columnFilter.value.dataSourceName.toLowerCase()))
  }
  // 前端分页
  columnTotal.value = data.length
  const start = (columnPageNum.value - 1) * columnPageSize.value
  const end = start + columnPageSize.value
  return data.slice(start, end).map(col => ({
    ...col,
    uniqueKey: `${col.tableId}-${col.columnName}` // 用于 row-key
  }))
})

// 弹窗和表单相关
const columns = ref([])
const currentTable = ref('')
const showColumns = ref(false)
const showForm = ref(false)
const formMode = ref('add')
const formRef = ref()
const form = ref({ id: undefined, dataSourceId: undefined, tableName: '', comment: '', databaseName: '' })
const rules = {
  dataSourceId: [{ required: true, message: '请选择数据源', trigger: 'change' }],
  tableName: [{ required: true, message: '请输入表名', trigger: 'blur' }],
}
const dsOptions = ref([])

// 视图模式切换
function handleViewModeChange(mode) {
  if (mode === 'column' && allColumns.value.length === 0) {
    getColumns()
  }
}

// 获取表数据
function getTables() {
  loading.value = true
  const params = { pageNum: pageNum.value, pageSize: pageSize.value }
  if (filterName.value) params.tableName = filterName.value
  if (filterDataSourceName.value) params.dataSourceName = filterDataSourceName.value
  if (filterDbName.value) params.databaseName = filterDbName.value
  if (Array.isArray(createRange.value) && createRange.value.length === 2) {
    params.createTimeStart = toISO(createRange.value[0])
    params.createTimeEnd = toISO(createRange.value[1])
  }
  if (Array.isArray(updateRange.value) && updateRange.value.length === 2) {
    params.updateTimeStart = toISO(updateRange.value[0])
    params.updateTimeEnd = toISO(updateRange.value[1])
  }
  listMetaTables(params).then(res => {
    tables.value = res.rows || []
    total.value = Number(res.total || 0)
  }).finally(() => (loading.value = false))
}

// 获取所有字段数据（字段查找模式）
function getColumns() {
  columnLoading.value = true
  listAllMetaColumns().then(res => {
    allColumns.value = res.rows || []
  }).finally(() => (columnLoading.value = false))
}

function openColumns(row) {
  currentTable.value = row.tableName
  const params = {
    dataSourceId: row.dataSourceId,
    tableName: row.tableName,
    databaseName: row.databaseName
  }
  listMetaColumns(params).then(res => {
    columns.value = res.rows || []
    showColumns.value = true
  })
}

// 字段查找模式下的方法
function queryColumns() {
  columnPageNum.value = 1
  // 前端过滤，computed 会自动更新
}

function resetColumnFilters() {
  columnFilter.value = {
    columnName: '',
    columnComment: '',
    tableName: '',
    dataSourceName: ''
  }
  columnPageNum.value = 1
}

function handleColumnSizeChange(size) {
  columnPageSize.value = size
  columnPageNum.value = 1
}

function handleColumnCurrentChange(page) {
  columnPageNum.value = page
}

// 从字段查找模式跳转到表查找模式
function goToTable(row) {
  viewMode.value = 'table'
  filterName.value = row.tableName
  filterDataSourceName.value = row.dataSourceName
  filterDbName.value = row.databaseName
  pageNum.value = 1
  getTables()
}

// 表查找模式下的分页方法
function handleSizeChange(size) {
  pageSize.value = size
  pageNum.value = 1
  getTables()
}

function handleCurrentChange(page) {
  pageNum.value = page
  getTables()
}

function toISO(d) {
  try {
    const dt = new Date(d)
    return dt.toISOString()
  } catch (e) {
    return undefined
  }
}

function queryTables() {
  pageNum.value = 1
  getTables()
}

function resetFilters() {
  filterName.value = ''
  filterDbName.value = ''
  filterDataSourceName.value = ''
  createRange.value = []
  updateRange.value = []
  pageNum.value = 1
  getTables()
}

function openAdd() {
  formMode.value = 'add'
  Object.assign(form.value, { id: undefined, dataSourceId: undefined, tableName: '', comment: '', databaseName: '' })
  showForm.value = true
}

function openEdit(row) {
  formMode.value = 'edit'
  Object.assign(form.value, {
    id: row.id,
    dataSourceId: row.dataSourceId,
    tableName: row.tableName,
    comment: row.comment || '',
    databaseName: row.databaseName || ''
  })
  showForm.value = true
}

function submitForm() {
  formRef.value?.validate(valid => {
    if (!valid) return
    const payload = { ...form.value }
    const req = formMode.value === 'add' ? addMetaTable(payload) : updateMetaTable(payload)
    req.then(() => {
      proxy.$modal.msgSuccess('操作成功')
      showForm.value = false
      getTables()
    })
  })
}

function confirmDelete(row) {
  proxy.$modal.confirm('确认删除该源数据表吗？').then(() => {
    delMetaTable(row.id).then(() => {
      proxy.$modal.msgSuccess('删除成功')
      getTables()
    })
  }).catch(() => {})
}

function loadDataSources() {
  listDatasource().then(res => {
    dsOptions.value = res.rows || []
  })
}

onMounted(() => {
  getTables()
  loadDataSources()
})
 </script>

 <style scoped>
 .prewrap { white-space: pre-wrap; word-break: break-word; }
 </style>
