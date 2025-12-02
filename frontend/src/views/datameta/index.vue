<template>
  <div class="app-container">
    <el-form :inline="true" style="margin-bottom: 12px">
      <el-form-item label="表名">
        <el-input v-model="filterName" placeholder="支持模糊匹配" style="width: 220px" />
      </el-form-item>
      <el-form-item label="数据库">
        <el-input v-model="filterDbName" placeholder="支持模糊匹配" style="width: 220px" />
      </el-form-item>
      <el-form-item label="创建时间">
        <el-date-picker v-model="createRange" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" style="width: 300px" />
      </el-form-item>
      <el-form-item label="修改时间">
        <el-date-picker v-model="updateRange" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" style="width: 300px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="queryTables">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="displayTables" row-key="id" style="width: 100%; margin-top: 12px" border>
      <el-table-column prop="tableName" label="表名" />
      <el-table-column prop="comment" label="表描述">
        <template #default="scope">
          <div class="prewrap">{{ scope.row.comment }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="databaseName" label="原始数据库" />
      <el-table-column prop="createTime" label="创建同步时间" />
      <el-table-column prop="updateTime" label="修改同步时间" />
      <el-table-column prop="createBy" label="采集人" />
      <el-table-column prop="updateBy" label="更新者" />
      <el-table-column label="操作" width="260">
        <template #default="scope">
          <el-button size="small" @click="openColumns(scope.row)">查看列</el-button>
          <el-button size="small" type="primary" @click="openEdit(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="confirmDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="display: flex; justify-content: flex-end; margin-top: 12px">
      <el-pagination
        :current-page="pageNum"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog v-model="showColumns" title="字段信息" width="70%">
      <div style="margin-bottom: 8px">当前表：{{ currentTable }}</div>
      <el-table :data="columns" border height="50vh">
        <el-table-column prop="columnIndex" label="序号" width="60" />
        <el-table-column prop="name" label="列名" />
        <el-table-column prop="comment" label="列描述">
          <template #default="scope"><div class="prewrap">{{ scope.row.comment }}</div></template>
        </el-table-column>
        <el-table-column prop="type" label="类型" />
        <el-table-column prop="notnull" label="非空" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.notnull ? 'danger' : 'info'">{{ scope.row.notnull ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="primary" label="主键" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.primary ? 'success' : 'info'">{{ scope.row.primary ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="default" label="默认值" />
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
        <el-form-item label="原始数据库" prop="databaseName">
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
import { listMetaTables, listMetaColumns, addMetaTable, updateMetaTable, delMetaTable } from '@/api/datameta'
import { listDatasource } from '@/api/datasource'
const { proxy } = getCurrentInstance()

const tables = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(10)
const filterName = ref('')
const filterDbName = ref('')
const createRange = ref([])
const updateRange = ref([])
const displayTables = computed(() => tables.value)
const columns = ref([])
const currentTable = ref('')
const loading = ref(false)
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


function getTables() {
  loading.value = true
  const params = { pageNum: pageNum.value, pageSize: pageSize.value }
  if (filterName.value) params.tableName = filterName.value
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

function openColumns(row) {
  currentTable.value = row.tableName
  const params = {
    dataSourceId: row.dataSourceId,
    tableName: row.tableName,
    databaseName: row.databaseName,
    pageNum: 1,
    pageSize: 1000
  }
  listMetaColumns(params).then(res => {
    columns.value = res.rows || []
    showColumns.value = true
  })
}

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
  listDatasource({ pageNum: 1, pageSize: 1000 }).then(res => {
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
