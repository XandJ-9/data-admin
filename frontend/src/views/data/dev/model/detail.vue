<template>
  <div class="app-container model-detail-page">
    <div class="page-header">
      <div>
        <h2>{{ isCreate ? '新建模型' : form.modelName || '模型详情' }}</h2>
        <p>在详情页维护表结构、字段注释与负责人，模型完成后再进入加工作业继续开发。</p>
      </div>
      <div class="header-actions">
        <el-button @click="goBack">返回</el-button>
        <el-button v-if="!isCreate && currentModelId" type="primary" plain @click="handleCreateJob">创建加工作业</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存模型</el-button>
        <el-button type="success" :loading="submitting" @click="handleSubmit">提交建表</el-button>
      </div>
    </div>

    <el-alert class="mb16" type="info" :closable="false" show-icon title="隐形治理前置" description="表注释、字段注释和负责人是模型发布前的必填治理项，提交建表和发布任务都会依赖这些信息。" />

    <el-card shadow="never" class="mb16">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="模型名称" prop="modelName">
              <el-input v-model="form.modelName" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模型编码" prop="modelCode">
              <el-input v-model="form.modelCode" :disabled="!isCreate" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="数据层级" prop="layer">
              <el-select v-model="form.layer" style="width: 100%">
                <el-option v-for="item in layerOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="执行引擎" prop="engineType">
              <el-select v-model="form.engineType" style="width: 100%">
                <el-option label="Spark SQL" value="spark" />
                <el-option label="Hive" value="hive" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="负责人" prop="owner">
              <el-input v-model="form.owner" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Schema/库" prop="schemaName">
              <el-input v-model="form.schemaName" placeholder="可选，如 dwd" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标表名" prop="tableName">
              <el-input v-model="form.tableName" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="表注释" prop="tableComment">
              <el-input v-model="form.tableComment" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="模型说明" prop="description">
              <el-input v-model="form.description" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card shadow="never" class="mb16">
      <template #header>
        <div class="section-header">
          <span>模型字段</span>
          <el-button type="primary" plain size="small" icon="Plus" @click="addFieldRow">新增字段</el-button>
        </div>
      </template>
      <el-table :data="fieldRows" border>
        <el-table-column label="序号" width="70">
          <template #default="scope">{{ scope.$index + 1 }}</template>
        </el-table-column>
        <el-table-column label="字段名" min-width="180">
          <template #default="scope">
            <el-input v-model="scope.row.fieldName" placeholder="如 order_id" />
          </template>
        </el-table-column>
        <el-table-column label="字段类型" min-width="160">
          <template #default="scope">
            <el-select v-model="scope.row.fieldType" filterable allow-create default-first-option style="width: 100%">
              <el-option v-for="item in fieldTypeOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="字段注释" min-width="220">
          <template #default="scope">
            <el-input v-model="scope.row.fieldComment" />
          </template>
        </el-table-column>
        <el-table-column label="可空" width="90">
          <template #default="scope">
            <el-switch v-model="scope.row.isNullable" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="scope">
            <el-button link type="danger" @click="removeFieldRow(scope.$index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span>DDL 预览</span>
      </template>
      <pre class="ddl-preview">{{ generatedSql }}</pre>
    </el-card>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { addModel, getModel, submitModel, updateModel } from '@/api/data/datadev'

defineOptions({ name: 'DataDevModelDetail' })

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const saving = ref(false)
const submitting = ref(false)
const currentModelId = ref(Number(route.params.modelId || 0))
const layerOptions = ['ODS', 'DWD', 'DWS', 'ADS']
const fieldTypeOptions = ['STRING', 'BIGINT', 'INT', 'DECIMAL(18,2)', 'DOUBLE', 'BOOLEAN', 'DATE', 'TIMESTAMP']
const form = reactive({
  modelName: '',
  modelCode: '',
  layer: 'DWD',
  tableName: '',
  schemaName: '',
  tableComment: '',
  engineType: 'spark',
  owner: '',
  description: '',
})
const fieldRows = ref([])
const rules = {
  modelName: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  modelCode: [{ required: true, message: '请输入模型编码', trigger: 'blur' }],
  layer: [{ required: true, message: '请选择数据层级', trigger: 'change' }],
  engineType: [{ required: true, message: '请选择执行引擎', trigger: 'change' }],
  tableName: [{ required: true, message: '请输入目标表名', trigger: 'blur' }],
  tableComment: [{ required: true, message: '请输入表注释', trigger: 'blur' }],
  owner: [{ required: true, message: '请输入负责人', trigger: 'blur' }],
}

const isCreate = computed(() => Number(route.params.modelId || 0) === 0 || route.query.mode === 'create')
const generatedSql = computed(() => {
  if (!fieldRows.value.length) return '-- 请先添加字段后再生成 DDL'
  const safeTableName = form.tableName || 'table_name'
  const fullTableName = form.schemaName ? `${form.schemaName}.${safeTableName}` : safeTableName
  const columns = fieldRows.value.map((field) => {
    const nullable = field.isNullable ? '' : ' NOT NULL'
    const comment = field.fieldComment ? ` COMMENT '${String(field.fieldComment).replace(/'/g, "''")}'` : ''
    return `  \`${field.fieldName || 'column_name'}\` ${field.fieldType || 'STRING'}${nullable}${comment}`
  }).join('\n')
  const tableComment = String(form.tableComment || '').replace(/'/g, "''")
  return [
    `CREATE TABLE IF NOT EXISTS ${fullTableName} (`,
    columns,
    ')',
    `COMMENT '${tableComment}'`,
  ].join('\n')
})

function addFieldRow() {
  fieldRows.value.push({ fieldName: '', fieldType: 'STRING', fieldComment: '', isNullable: true })
}

function removeFieldRow(index) {
  fieldRows.value.splice(index, 1)
}

function goBack() {
  router.push('/datadev/modeling')
}

function handleCreateJob() {
  if (!currentModelId.value) return
  router.push({ path: '/datadev/ide', query: { quickCreate: 'sql', targetModelId: currentModelId.value } })
}

function buildPayload() {
  return {
    ...form,
    fields: fieldRows.value.map((field, index) => ({
      fieldName: field.fieldName,
      fieldType: field.fieldType,
      fieldComment: field.fieldComment,
      isNullable: field.isNullable,
      ordinalPosition: index + 1,
    })),
  }
}

async function validatePayload() {
  await formRef.value?.validate()
  if (!fieldRows.value.length) {
    throw new Error('请至少配置一个字段')
  }
  fieldRows.value.forEach((field, index) => {
    if (!field.fieldName) {
      throw new Error(`第 ${index + 1} 个字段缺少字段名`)
    }
    if (!field.fieldComment) {
      throw new Error(`第 ${index + 1} 个字段缺少字段注释`)
    }
  })
}

async function saveOrUpdateModel() {
  await validatePayload()
  const payload = buildPayload()
  if (isCreate.value || !currentModelId.value) {
    const res = await addModel(payload)
    currentModelId.value = res.data.modelId
    await router.replace(`/datadev/modeling/detail/${currentModelId.value}`)
    return currentModelId.value
  }
  await updateModel(currentModelId.value, payload)
  return currentModelId.value
}

async function loadDetail() {
  if (isCreate.value) {
    if (!fieldRows.value.length) addFieldRow()
    return
  }
  const res = await getModel(route.params.modelId)
  const data = res.data || {}
  currentModelId.value = data.modelId
  form.modelName = data.modelName || ''
  form.modelCode = data.modelCode || ''
  form.layer = data.layer || 'DWD'
  form.tableName = data.tableName || ''
  form.schemaName = data.schemaName || ''
  form.tableComment = data.tableComment || ''
  form.engineType = data.engineType || 'spark'
  form.owner = data.owner || ''
  form.description = data.description || ''
  fieldRows.value = (data.fields || []).map((item) => ({
    fieldName: item.fieldName,
    fieldType: item.fieldType,
    fieldComment: item.fieldComment,
    isNullable: item.isNullable,
  }))
  if (!fieldRows.value.length) addFieldRow()
}

async function handleSave() {
  saving.value = true
  try {
    await saveOrUpdateModel()
    ElMessage.success('模型保存成功')
  } catch (error) {
    ElMessage.error(error.message || '模型保存失败')
  } finally {
    saving.value = false
  }
}

async function handleSubmit() {
  submitting.value = true
  try {
    const modelId = await saveOrUpdateModel()
    const res = await submitModel(modelId)
    ElMessage.success(res.msg || '提交建表成功')
    await loadDetail()
  } catch (error) {
    ElMessage.error(error.message || '提交建表失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadDetail)
</script>
