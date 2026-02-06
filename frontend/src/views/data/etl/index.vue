<!-- eslint-disable vue/no-v-model-argument -->
<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <el-form v-if="showSearch" :model="queryParams" ref="queryRef" :inline="true">
      <el-form-item label="任务名称" prop="taskName">
        <el-input v-model="queryParams.taskName" placeholder="请输入任务名称" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="任务编码" prop="taskCode">
        <el-input v-model="queryParams.taskCode" placeholder="请输入任务编码" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="ETL类型" prop="etlType">
        <el-select v-model="queryParams.etlType" placeholder="请选择ETL类型" clearable style="width: 200px">
          <el-option label="STG采集" value="extract" />
          <el-option label="DWD转换" value="transform" />
          <el-option label="ODS加载" value="load" />
          <el-option label="全量ETL" value="full" />
        </el-select>
      </el-form-item>
      <el-form-item label="执行器类型" prop="executorType">
        <el-select v-model="queryParams.executorType" placeholder="请选择执行器类型" clearable style="width: 200px">
          <el-option label="模拟执行器" value="mock" />
          <el-option label="DataX" value="datax" />
          <el-option label="Spark SQL" value="spark" />
          <el-option label="Python脚本" value="python" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="请选择状态" clearable style="width: 200px">
          <el-option label="启用" value="0" />
          <el-option label="停用" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 工具栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['system:dataetl:task:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['system:dataetl:task:remove']">删除</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="success" plain icon="VideoPlay" :disabled="single" @click="handleExecute" v-hasPermi="['system:dataetl:task:execute']">执行</el-button>
      </el-col>
      <right-toolbar :showSearch="showSearch" @update:showSearch="val => (showSearch = val)" @queryTable="getList" />
    </el-row>

    <!-- 列表 -->
    <el-table v-loading="loading" :data="dataList" @selection-change="handleSelectionChange" border>
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="任务名称" prop="taskName" width="180" :show-overflow-tooltip="true" />
      <el-table-column label="任务编码" prop="taskCode" width="150" :show-overflow-tooltip="true" />
      <el-table-column label="ETL类型" prop="etlType" width="120">
        <template #default="scope">
          <dict-tag :options="etl_type_options" :value="scope.row.etlType" />
        </template>
      </el-table-column>
      <el-table-column label="执行器类型" prop="executorType" width="120">
        <template #default="scope">
          <dict-tag :options="executor_type_options" :value="scope.row.executorType" />
        </template>
      </el-table-column>
      <el-table-column label="源数据源" prop="sourceDatasourceName" width="150" :show-overflow-tooltip="true" />
      <el-table-column label="目标数据源" prop="targetDatasourceName" width="150" :show-overflow-tooltip="true" />
      <el-table-column label="源表" prop="sourceTableName" width="150" :show-overflow-tooltip="true" />
      <el-table-column label="目标表" prop="targetTable" width="150" :show-overflow-tooltip="true" />
      <el-table-column label="状态" prop="status" width="80">
        <template #default="scope">
          <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
        </template>
      </el-table-column>
      <el-table-column label="创建时间" align="center" prop="createTime" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="280" fixed="right">
        <template #default="scope">
          <el-button link size="small" type="primary" icon="View" @click="handleDetail(scope.row)">详情</el-button>
          <el-button link size="small" type="primary" icon="VideoPlay" @click="handleExecute(scope.row)" v-hasPermi="['system:dataetl:task:execute']">执行</el-button>
          <el-button link size="small" type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['system:dataetl:task:edit']">修改</el-button>
          <el-button link size="small" type="success" icon="Clock" @click="handleVersion(scope.row)">版本</el-button>
          <el-button link size="small" type="danger" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['system:dataetl:task:remove']">删除</el-button>
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
    <el-dialog :title="title" v-model="open" width="900px" append-to-body>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="140px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务名称" prop="taskName">
              <el-input v-model="form.taskName" placeholder="请输入任务名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务编码" prop="taskCode">
              <el-input v-model="form.taskCode" placeholder="请输入任务编码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ETL类型" prop="etlType">
              <el-select v-model="form.etlType" placeholder="请选择ETL类型">
                <el-option v-for="dict in etl_type_options" :key="dict.value" :label="dict.label" :value="dict.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="执行器类型" prop="executorType">
              <el-select v-model="form.executorType" placeholder="请选择执行器类型">
                <el-option v-for="dict in executor_type_options" :key="dict.value" :label="dict.label" :value="dict.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="执行策略" prop="executeStrategy">
              <el-select v-model="form.executeStrategy" placeholder="请选择执行策略">
                <el-option label="全量" value="full" />
                <el-option label="增量" value="increment" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="源数据源" prop="sourceDatasourceId">
              <el-select v-model="form.sourceDatasourceId" filterable placeholder="请选择源数据源" @change="handleSourceDatasourceChange">
                <el-option v-for="ds in datasourceOptions" :key="ds.dataSourceId" :label="ds.dataSourceName" :value="ds.dataSourceId" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标数据源" prop="targetDatasourceId">
              <el-select v-model="form.targetDatasourceId" filterable placeholder="请选择目标数据源" @change="handleTargetDatasourceChange">
                <el-option v-for="ds in datasourceOptions" :key="ds.dataSourceId" :label="ds.dataSourceName" :value="ds.dataSourceId" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="源表" prop="sourceTableId">
              <el-select v-model="form.sourceTableId" filterable placeholder="请选择源表" :disabled="!form.sourceDatasourceId">
                <el-option v-for="table in sourceTableOptions" :key="table.id" :label="table.tableName" :value="table.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标表" prop="targetTable">
              <el-select
                v-model="form.targetTable"
                filterable
                placeholder="请选择目标表"
                :disabled="!form.targetDatasourceId"
                allow-create
              >
                <el-option v-for="table in targetTableOptions" :key="table.id" :label="table.tableName" :value="table.tableName" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="任务描述">
              <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入任务描述" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="SQL配置">
              <el-input v-model="form.sqlConfig" type="textarea" :rows="4" placeholder="请输入SQL配置" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-radio-group v-model="form.status">
                <el-radio v-for="dict in sys_normal_disable" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
              </el-radio-group>
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

    <!-- 任务详情弹窗 -->
    <el-dialog title="任务详情" v-model="detailOpen" width="900px" append-to-body>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务名称">{{ detailData.taskName }}</el-descriptions-item>
        <el-descriptions-item label="任务编码">{{ detailData.taskCode }}</el-descriptions-item>
        <el-descriptions-item label="ETL类型">
          <dict-tag :options="etl_type_options" :value="detailData.etlType" />
        </el-descriptions-item>
        <el-descriptions-item label="执行器类型">
          <dict-tag :options="executor_type_options" :value="detailData.executorType" />
        </el-descriptions-item>
        <el-descriptions-item label="执行策略">{{ detailData.executeStrategy === 'full' ? '全量' : '增量' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <dict-tag :options="sys_normal_disable" :value="detailData.status" />
        </el-descriptions-item>
        <el-descriptions-item label="源数据源">{{ detailData.sourceDatasourceName }}</el-descriptions-item>
        <el-descriptions-item label="目标数据源">{{ detailData.targetDatasourceName }}</el-descriptions-item>
        <el-descriptions-item label="源表">{{ detailData.sourceTableName }}</el-descriptions-item>
        <el-descriptions-item label="目标表">{{ detailData.targetTable }}</el-descriptions-item>
        <el-descriptions-item label="任务描述" :span="2">{{ detailData.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="SQL配置" :span="2">
          <pre style="white-space: pre-wrap; word-wrap: break-word;">{{ detailData.sqlConfig || '-' }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="创建者">{{ detailData.createBy }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailData.createTime }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detailData.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailOpen = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 版本管理弹窗 -->
    <el-dialog title="版本管理" v-model="versionOpen" width="900px" append-to-body>
      <div style="margin-bottom: 15px;">
        <el-button type="primary" icon="Plus" size="small" @click="handleCreateVersion">创建版本快照</el-button>
      </div>
      <el-table :data="versionList" border>
        <el-table-column label="版本号" prop="versionNumber" width="100" align="center" />
        <el-table-column label="是否当前版本" prop="isCurrent" width="120" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.isCurrent" type="success">当前版本</el-tag>
            <el-tag v-else type="info">历史版本</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="变更日志" prop="changeLog" :show-overflow-tooltip="true" />
        <el-table-column label="创建者" prop="createBy" width="120" align="center" />
        <el-table-column label="创建时间" prop="createTime" width="180" align="center" />
        <el-table-column label="操作" align="center" width="150" fixed="right">
          <template #default="scope">
            <el-button
              v-if="!scope.row.isCurrent"
              link
              size="small"
              type="primary"
              icon="RefreshLeft"
              @click="handleRollback(scope.row)"
            >回滚</el-button>
            <span v-else style="color: #909399;">当前版本</span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="versionOpen = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 创建版本弹窗 -->
    <el-dialog title="创建版本快照" v-model="createVersionOpen" width="500px" append-to-body>
      <el-form ref="versionFormRef" :model="versionForm" :rules="versionRules" label-width="100px">
        <el-form-item label="变更日志" prop="changeLog">
          <el-input v-model="versionForm.changeLog" type="textarea" :rows="4" placeholder="请输入本次变更的说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitVersion">确 定</el-button>
          <el-button @click="createVersionOpen = false">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="ETLTask">
import { getCurrentInstance } from 'vue'
import { listDatasource, listMetaTables } from '@/api/data/asset'
import {
  listETLTask,
  getETLTask,
  addETLTask,
  updateETLTask,
  delETLTask,
  executeETLTask,
  createETLTaskVersion,
  listETLTaskVersion,
  rollbackETLTaskVersion
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
const detailOpen = ref(false)
const detailData = ref({})

const datasourceOptions = ref([])
const sourceTableOptions = ref([])
const targetTableOptions = ref([])

// 版本管理
const versionOpen = ref(false)
const createVersionOpen = ref(false)
const versionList = ref([])
const currentTaskId = ref(null)
const versionForm = ref({})
const versionRules = ref({
  changeLog: [
    { required: true, message: '变更日志不能为空', trigger: 'blur' }
  ]
})

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  taskName: undefined,
  taskCode: undefined,
  etlType: undefined,
  executorType: undefined,
  status: undefined
})

const form = ref({})
const rules = ref({
  taskName: [
    { required: true, message: '任务名称不能为空', trigger: 'blur' }
  ],
  taskCode: [
    { required: true, message: '任务编码不能为空', trigger: 'blur' }
  ],
  etlType: [
    { required: true, message: '请选择ETL类型', trigger: 'change' }
  ],
  executorType: [
    { required: true, message: '请选择执行器类型', trigger: 'change' }
  ],
  executeStrategy: [
    { required: true, message: '请选择执行策略', trigger: 'change' }
  ],
  sourceDatasourceId: [
    { required: true, message: '请选择源数据源', trigger: 'change' }
  ],
  targetDatasourceId: [
    { required: true, message: '请选择目标数据源', trigger: 'change' }
  ],
  sourceTableId: [
    { required: true, message: '请选择源表', trigger: 'change' }
  ],
  targetTable: [
    { required: true, message: '请输入目标表名', trigger: 'blur' }
  ]
})

// 字典选项
const etl_type_options = ref([
  { label: 'STG采集', value: 'extract' },
  { label: 'DWD转换', value: 'transform' },
  { label: 'ODS加载', value: 'load' },
  { label: '全量ETL', value: 'full' }
])

const executor_type_options = ref([
  { label: '模拟执行器', value: 'mock' },
  { label: 'DataX', value: 'datax' },
  { label: 'Spark SQL', value: 'spark' },
  { label: 'Python脚本', value: 'python' }
])

const { sys_normal_disable } = proxy.useDict('sys_normal_disable')

/** 查询ETL任务列表 */
function getList() {
  loading.value = true
  listETLTask(queryParams.value).then(res => {
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
    taskId: undefined,
    taskName: undefined,
    taskCode: undefined,
    description: undefined,
    etlType: 'full',
    executorType: 'mock',
    executeStrategy: 'full',
    sourceDatasourceId: undefined,
    targetDatasourceId: undefined,
    sourceTableId: undefined,
    targetTable: undefined,
    sqlConfig: undefined,
    executorParams: undefined,
    status: '0',
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
  ids.value = selection.map(item => item.taskId)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

/** 新增按钮操作 */
function handleAdd() {
  reset()
  open.value = true
  title.value = '新增ETL任务'
}

/** 修改按钮操作 */
function handleUpdate(row) {
  reset()
  const taskId = row.taskId || ids.value[0]
  getETLTask(taskId).then(res => {
    form.value = res.data
    // 加载源表列表
    if (form.value.sourceDatasourceId) {
      loadSourceTables(form.value.sourceDatasourceId)
    }
    // 加载目标表列表
    if (form.value.targetDatasourceId) {
      loadTargetTables(form.value.targetDatasourceId)
    }
    open.value = true
    title.value = '修改ETL任务'
  })
}

/** 详情按钮操作 */
function handleDetail(row) {
  const taskId = row.taskId
  getETLTask(taskId).then(res => {
    detailData.value = res.data
    detailOpen.value = true
  })
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs['formRef'].validate(valid => {
    if (valid) {
      if (form.value.taskId) {
        updateETLTask(form.value).then(() => {
          proxy.$modal.msgSuccess('修改成功')
          open.value = false
          getList()
        })
      } else {
        addETLTask(form.value).then(() => {
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
  const taskIds = row.taskId || ids.value
  proxy.$modal.confirm('是否确认删除ETL任务编号为"' + taskIds + '"的数据项？').then(() => {
    return delETLTask(taskIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

/** 执行按钮操作 */
function handleExecute(row) {
  const taskId = row.taskId || ids.value[0]
  proxy.$modal.confirm('是否确认执行ETL任务"' + row.taskName + '"？').then(() => {
    return executeETLTask(taskId)
  }).then(res => {
    proxy.$modal.msgSuccess('任务已提交执行，执行ID: ' + res.data.executionId)
  }).catch(() => {})
}

/** 源数据源变化 */
function handleSourceDatasourceChange(value) {
  form.value.sourceTableId = undefined
  if (value) {
    loadSourceTables(value)
  } else {
    sourceTableOptions.value = []
  }
}

/** 目标数据源变化 */
function handleTargetDatasourceChange(value) {
  form.value.targetTable = undefined
  if (value) {
    loadTargetTables(value)
  } else {
    targetTableOptions.value = []
  }
}

/** 加载源表列表 */
function loadSourceTables(datasourceId) {
  listMetaTables({ dataSourceId: datasourceId }).then(res => {
    sourceTableOptions.value = res.rows || []
  })
}

/** 加载目标表列表 */
function loadTargetTables(datasourceId) {
  listMetaTables({ dataSourceId: datasourceId }).then(res => {
    targetTableOptions.value = res.rows || []
  })
}

/** 获取数据源列表 */
function getDatasourceList() {
  listDatasource().then(res => {
    datasourceOptions.value = res.rows || []
  })
}

/** 版本管理按钮操作 */
function handleVersion(row) {
  currentTaskId.value = row.taskId
  getVersionList()
  versionOpen.value = true
}

/** 获取版本列表 */
function getVersionList() {
  listETLTaskVersion(currentTaskId.value).then(res => {
    versionList.value = res.data || []
  })
}

/** 创建版本快照 */
function handleCreateVersion() {
  versionForm.value = {
    changeLog: undefined
  }
  createVersionOpen.value = true
}

/** 提交版本 */
function submitVersion() {
  proxy.$refs['versionFormRef'].validate(valid => {
    if (valid) {
      createETLTaskVersion(currentTaskId.value, versionForm.value).then(() => {
        proxy.$modal.msgSuccess('版本创建成功')
        createVersionOpen.value = false
        getVersionList()
      })
    }
  })
}

/** 回滚版本 */
function handleRollback(row) {
  proxy.$modal.confirm('是否确认回滚到版本"' + row.versionNumber + '"？').then(() => {
    return rollbackETLTaskVersion(currentTaskId.value, { versionNumber: row.versionNumber })
  }).then(() => {
    proxy.$modal.msgSuccess('回滚成功')
    getVersionList()
    getList()
  }).catch(() => {})
}

onMounted(() => {
  getList()
  getDatasourceList()
})
</script>
