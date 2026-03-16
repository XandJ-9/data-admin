<!-- eslint-disable vue/no-v-model-argument -->
<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <el-form v-if="showSearch" :model="queryParams" ref="queryRef" :inline="true">
      <el-form-item label="ETL任务" prop="taskId">
        <el-select v-model="queryParams.taskId" placeholder="请选择任务" clearable filterable style="width: 200px">
          <el-option v-for="task in taskOptions" :key="task.taskId" :label="task.taskName" :value="task.taskId" />
        </el-select>
      </el-form-item>
      <el-form-item label="源字段名" prop="sourceFieldName">
        <el-input v-model="queryParams.sourceFieldName" placeholder="请输入源字段名" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="目标字段名" prop="targetFieldName">
        <el-input v-model="queryParams.targetFieldName" placeholder="请输入目标字段名" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 工具栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['system:dataetl:fieldmapping:edit']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['system:dataetl:fieldmapping:edit']">删除</el-button>
      </el-col>
      <right-toolbar :showSearch="showSearch" @update:showSearch="val => (showSearch = val)" @queryTable="getList" />
    </el-row>

    <!-- 列表 -->
    <el-table v-loading="loading" :data="dataList" @selection-change="handleSelectionChange" border>
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="任务名称" prop="taskName" width="180" :show-overflow-tooltip="true" />
      <el-table-column label="源字段名" prop="sourceFieldName" width="150" :show-overflow-tooltip="true" />
      <el-table-column label="目标字段名" prop="targetFieldName" width="150" :show-overflow-tooltip="true" />
      <el-table-column label="转换规则" prop="transformRule" width="200" :show-overflow-tooltip="true" />
      <el-table-column label="清洗规则" prop="cleanRule" width="150" :show-overflow-tooltip="true" />
      <el-table-column label="数据类型" prop="dataType" width="120" />
      <el-table-column label="是否主键" prop="isPrimaryKey" width="100" align="center">
        <template #default="scope">
          <el-tag v-if="scope.row.isPrimaryKey" type="success">是</el-tag>
          <el-tag v-else type="info">否</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="排序" prop="sortOrder" width="80" align="center" />
      <el-table-column label="备注" prop="remark" width="150" :show-overflow-tooltip="true" />
      <el-table-column label="操作" align="center" width="150" fixed="right">
        <template #default="scope">
          <el-button link size="small" type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['system:dataetl:fieldmapping:edit']">修改</el-button>
          <el-button link size="small" type="danger" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['system:dataetl:fieldmapping:edit']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      v-show="total > 0"
      :total="total"
      :page="queryParams.pageNum"
      :limit="queryParams.pageSize"
      @update:page="val => (queryParams.pageNum = val)"
      @update:limit="val => (queryParams.pageSize = val)"
      @pagination="getList"
    />

    <!-- 新增/修改弹窗 -->
    <el-dialog :title="title" v-model="open" width="700px" append-to-body>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="ETL任务" prop="taskId">
              <el-select v-model="form.taskId" filterable placeholder="请选择ETL任务" :disabled="form.mappingId !== undefined">
                <el-option v-for="task in taskOptions" :key="task.taskId" :label="task.taskName" :value="task.taskId" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="源字段名" prop="sourceFieldName">
              <el-input v-model="form.sourceFieldName" placeholder="请输入源字段名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标字段名" prop="targetFieldName">
              <el-input v-model="form.targetFieldName" placeholder="请输入目标字段名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据类型" prop="dataType">
              <el-input v-model="form.dataType" placeholder="例如: VARCHAR(100)" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序" prop="sortOrder">
              <el-input-number v-model="form.sortOrder" :min="0" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="转换规则">
              <el-input v-model="form.transformRule" type="textarea" :rows="2" placeholder="例如: CAST AS BIGINT, UPPER, TRIM" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="清洗规则">
              <el-input v-model="form.cleanRule" type="textarea" :rows="2" placeholder="例如: 去除空格、默认值设置等" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否主键">
              <el-switch v-model="form.isPrimaryKey" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="请输入备注" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="ETLFieldMapping">
import { getCurrentInstance } from 'vue'
import { listETLTaskSimple ,
  listETLFieldMapping,
  getETLFieldMapping,
  addETLFieldMapping,
  updateETLFieldMapping,
  delETLFieldMapping
} from '@/api/data/etl'

const { proxy } = getCurrentInstance()

const dataList = ref([])
const loading = ref(false)
const showSearch = ref(true)
const ids = ref([])
const single = ref(true)
const multiple = ref(true)
const total = ref(0)
const title = ref('')
const open = ref(false)

const taskOptions = ref([])

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  taskId: undefined,
  sourceFieldName: undefined,
  targetFieldName: undefined
})

const form = ref({})
const rules = ref({
  taskId: [
    { required: true, message: 'ETL任务不能为空', trigger: 'change' }
  ],
  sourceFieldName: [
    { required: true, message: '源字段名不能为空', trigger: 'blur' }
  ],
  targetFieldName: [
    { required: true, message: '目标字段名不能为空', trigger: 'blur' }
  ]
})

/** 查询字段映射列表 */
function getList() {
  loading.value = true
  listETLFieldMapping(queryParams.value).then(res => {
    dataList.value = res.rows || []
    total.value = res.total || 0
    loading.value = false
  }).catch(() => {
    loading.value = false
  })
}

/** 取消按钮 */
function cancel() {
  open.value = false
  reset()
}

/** 表单重置 */
function reset() {
  form.value = {
    mappingId: undefined,
    taskId: undefined,
    sourceFieldName: undefined,
    targetFieldName: undefined,
    transformRule: undefined,
    cleanRule: undefined,
    dataType: undefined,
    isPrimaryKey: false,
    sortOrder: 0,
    remark: undefined
  }
  proxy.resetForm('formRef')
}

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.mappingId)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

/** 新增按钮操作 */
function handleAdd() {
  reset()
  open.value = true
  title.value = '新增字段映射'
}

/** 修改按钮操作 */
function handleUpdate(row) {
  reset()
  const mappingId = row.mappingId || ids.value[0]
  getETLFieldMapping(mappingId).then(res => {
    form.value = res.data
    open.value = true
    title.value = '修改字段映射'
  })
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs['formRef'].validate(valid => {
    if (valid) {
      if (form.value.mappingId) {
        updateETLFieldMapping(form.value).then(() => {
          proxy.$modal.msgSuccess('修改成功')
          open.value = false
          getList()
        })
      } else {
        addETLFieldMapping(form.value).then(() => {
          proxy.$modal.msgSuccess('新增成功')
          open.value = false
          getList()
        })
      }
    }
  })
}

/** 删除按钮操作 */
function handleDelete(row) {
  const mappingIds = row.mappingId || ids.value
  proxy.$modal.confirm('是否确认删除字段映射编号为"' + mappingIds + '"的数据项？').then(() => {
    return delETLFieldMapping(mappingIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

/** 获取任务列表（用于下拉框） */
function getTaskList() {
  listETLTaskSimple().then(res => {
    taskOptions.value = res.data || []
  })
}

onMounted(() => {
  getList()
  getTaskList()
})
</script>
