<template>
  <div class="app-container">
    <!-- 工具栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd">新增血缘</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete">删除</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="info" plain icon="Share" @click="showGraphDialog = true">血缘图</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList" />
    </el-row>

    <!-- 搜索表单 -->
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="源表" prop="sourceTableName">
        <el-input
          v-model="queryParams.sourceTableName"
          placeholder="请输入源表名"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="目标表" prop="targetTableName">
        <el-input
          v-model="queryParams.targetTableName"
          placeholder="请输入目标表名"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="血缘类型" prop="lineageType">
        <el-select v-model="queryParams.lineageType" placeholder="请选择血缘类型" clearable style="width: 150px">
          <el-option label="上游" value="upstream" />
          <el-option label="下游" value="downstream" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="dataList"
      @selection-change="handleSelectionChange"
      border
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="ID" align="center" prop="id" width="80" />
      <el-table-column label="源表" align="center" prop="sourceTableName" min-width="150" show-overflow-tooltip />
      <el-table-column label="目标表" align="center" prop="targetTableName" min-width="150" show-overflow-tooltip />
      <el-table-column label="血缘类型" align="center" prop="lineageType" width="100">
        <template #default="scope">
          <el-tag v-if="scope.row.lineageType === 'upstream'" type="success">上游</el-tag>
          <el-tag v-else type="info">下游</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="描述" align="center" prop="description" min-width="200" show-overflow-tooltip />
      <el-table-column label="创建时间" align="center" prop="createTime" width="180" />
      <el-table-column label="操作" align="center" width="200" fixed="right">
        <template #default="scope">
          <el-button
            link
            type="primary"
            icon="View"
            @click="handleView(scope.row)"
          >查看</el-button>
          <el-button
            link
            type="primary"
            icon="Edit"
            @click="handleUpdate(scope.row)"
          >修改</el-button>
          <el-button
            link
            type="danger"
            icon="Delete"
            @click="handleDelete(scope.row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 添加/修改对话框 -->
    <LineageFormDialog
      v-model="open"
      :title="title"
      :form="form"
      :rules="rules"
      :table-options="tableOptions"
      @submit="handleFormSubmit"
    />

    <!-- 血缘图对话框 -->
    <LineageGraphDialog v-model="showGraphDialog" :table-options="tableOptions" />
  </div>
</template>

<script setup name="TableLineage">
import {
  listTableLineage,
  getTableLineage,
  addTableLineage,
  updateTableLineage,
  delTableLineage
} from '@/api/data/asset'
import { listMetaTables } from '@/api/data/asset'
import LineageFormDialog from './LineageFormDialog.vue'
import LineageGraphDialog from './LineageGraphDialog.vue'

const { proxy } = getCurrentInstance()

const dataList = ref([])
const open = ref(false)
const showSearch = ref(true)
const showGraphDialog = ref(false)
const title = ref('')
const loading = ref(false)
const total = ref(0)
const ids = ref([])
const single = ref(true)
const multiple = ref(true)
const tableOptions = ref([])

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  sourceTableName: null,
  targetTableName: null,
  lineageType: null
})

const form = ref({})
const rules = ref({
  sourceTableId: [{ required: true, message: '源表不能为空', trigger: 'change' }],
  targetTableId: [{ required: true, message: '目标表不能为空', trigger: 'change' }],
  lineageType: [{ required: true, message: '血缘类型不能为空', trigger: 'change' }]
})

function getList() {
  loading.value = true
  listTableLineage(queryParams.value)
    .then(response => {
      dataList.value = response.rows
      total.value = response.total
    })
    .catch(() => {})
    .finally(() => { loading.value = false })
}

function reset() {
  form.value = {
    id: null,
    sourceTableId: null,
    targetTableId: null,
    lineageType: 'upstream',
    description: null
  }
  proxy.resetForm('formRef')
}

function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
}

function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.id)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

function handleAdd() {
  reset()
  loadTableOptions()
  open.value = true
  title.value = '添加表血缘'
}

function handleUpdate(row) {
  reset()
  loadTableOptions()
  getTableLineage(row.id || ids.value[0]).then(response => {
    form.value = response.data
    open.value = true
    title.value = '修改表血缘'
  })
}

function handleView(row) {
  reset()
  getTableLineage(row.id).then(response => {
    form.value = response.data
    open.value = true
    title.value = '查看表血缘'
  })
}

function handleFormSubmit() {
  const api = form.value.id ? updateTableLineage : addTableLineage
  api(form.value).then(() => {
    proxy.$modal.msgSuccess(form.value.id ? '修改成功' : '新增成功')
    open.value = false
    getList()
  })
}

function handleDelete(row) {
  const deleteIds = row.id || ids.value.join(',')
  proxy.$modal.confirm('是否确认删除选中的数据项？').then(() => {
    return delTableLineage(deleteIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

function loadTableOptions() {
  if (tableOptions.value.length > 0) return
  listMetaTables({ pageNum: 1, pageSize: 10000 }).then(response => {
    tableOptions.value = response.rows
  })
}

getList()
</script>

