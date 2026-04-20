<template>
  <div class="app-container">
    <el-form v-show="showSearch" ref="queryRef" :inline="true" :model="queryParams">
      <el-form-item label="模型名称" prop="modelName">
        <el-input v-model="queryParams.modelName" placeholder="请输入模型名称" clearable style="width: 220px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="数据层级" prop="layer">
        <el-select v-model="queryParams.layer" placeholder="请选择层级" clearable style="width: 160px">
          <el-option v-for="item in layerOptions" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="请选择状态" clearable style="width: 160px">
          <el-option label="草稿" value="draft" />
          <el-option label="已建表" value="deployed" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" v-hasPermi="['datadev:model:add']" @click="handleAdd">新增模型</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList" />
    </el-row>

    <el-table v-loading="loading" :data="modelList" border>
      <el-table-column prop="modelName" label="模型名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="modelCode" label="模型编码" min-width="160" show-overflow-tooltip />
      <el-table-column prop="layer" label="层级" width="100" />
      <el-table-column prop="tableName" label="目标表" min-width="180" show-overflow-tooltip />
      <el-table-column prop="engineType" label="执行引擎" width="120">
        <template #default="scope">{{ scope.row.engineType === 'spark' ? 'Spark SQL' : 'Hive' }}</template>
      </el-table-column>
      <el-table-column prop="fieldCount" label="字段数" width="90" />
      <el-table-column prop="owner" label="负责人" width="140" />
      <el-table-column prop="status" label="状态" width="110">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'deployed' ? 'success' : 'info'" effect="plain">{{ scope.row.status === 'deployed' ? '已建表' : '草稿' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updateTime" label="更新时间" width="180" />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="scope">
          <el-button link type="primary" v-hasPermi="['datadev:model:query']" @click="handleDetail(scope.row)">详情</el-button>
          <el-button link type="success" v-hasPermi="['datadev:model:submit']" @click="handleSubmit(scope.row)">提交建表</el-button>
          <el-button link type="danger" v-hasPermi="['datadev:model:remove']" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />
  </div>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { listModels, delModel, submitModel } from '@/api/data/datadev'

defineOptions({ name: 'DataDevModeling' })

const router = useRouter()
const loading = ref(false)
const showSearch = ref(true)
const total = ref(0)
const modelList = ref([])
const layerOptions = ['ODS', 'DWD', 'DWS', 'ADS']
const queryRef = ref(null)
const queryParams = reactive({ pageNum: 1, pageSize: 10, modelName: '', layer: '', status: '' })

async function getList() {
  loading.value = true
  try {
    const res = await listModels(queryParams)
    modelList.value = res.rows || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function handleQuery() {
  queryParams.pageNum = 1
  getList()
}

function resetQuery() {
  queryRef.value?.resetFields()
  handleQuery()
}

function handleAdd() {
  router.push('/datadev/modeling/detail/0?mode=create')
}

function handleDetail(row) {
  router.push(`/datadev/modeling/detail/${row.modelId}`)
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`是否确认删除模型“${row.modelName}”？`, '提示', { type: 'warning' })
    await delModel(row.modelId)
    ElMessage.success('删除成功')
    await getList()
  } catch {}
}

async function handleSubmit(row) {
  try {
    await ElMessageBox.confirm(`确认提交模型“${row.modelName}”并创建数据表吗？`, '提交建表', { type: 'warning' })
    await submitModel(row.modelId)
    ElMessage.success('提交建表成功')
    await getList()
  } catch {}
}

onMounted(getList)
</script>
