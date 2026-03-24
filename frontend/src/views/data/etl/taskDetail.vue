<template>
  <div class="app-container etl-task-detail">
    <!-- 页面头部 -->
    <el-page-header @back="handleBack" class="page-header">
      <template #content>
        <div class="header-content">
          <span v-if="!isEdit">{{ taskForm.taskName || '新建ETL任务' }}</span>
          <el-input
            v-else
            v-model="taskForm.taskName"
            placeholder="请输入任务名称"
            style="width: 300px"
          />
        </div>
      </template>
      <template #extra>
        <div class="header-actions">
          <template v-if="isEdit">
            <el-button @click="isEdit = false">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
          </template>
          <template v-else>
            <el-button @click="handleExecute" :disabled="taskForm.status !== '0'">
              <el-icon><VideoPlay /></el-icon> 执行任务
            </el-button>
            <el-button @click="isEdit = true">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-dropdown @command="handleMoreCommand">
              <el-button>
                更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="clone">克隆任务</el-dropdown-item>
                  <el-dropdown-item command="version">版本管理</el-dropdown-item>
                  <el-dropdown-item command="validate">验证配置</el-dropdown-item>
                  <el-dropdown-item command="datx" divided>生成DataX配置</el-dropdown-item>
                  <el-dropdown-item command="dryRun">模拟执行</el-dropdown-item>
                  <el-dropdown-item command="delete" divided style="color: #f56c6c">删除任务</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </div>
      </template>
    </el-page-header>

    <!-- 任务状态标签 -->
    <div class="task-status-bar">
      <el-tag :type="taskForm.status === '0' ? 'success' : 'danger'" size="large">
        {{ taskForm.status === '0' ? '已启用' : '已停用' }}
      </el-tag>
      <el-tag v-if="taskForm.etlType" :type="getEtlTypeColor(taskForm.etlType)" size="large">
        {{ getEtlTypeText(taskForm.etlType) }}
      </el-tag>
      <el-tag size="large">{{ getExecutorTypeText(taskForm.executorType) }}</el-tag>
      <el-tag :type="taskForm.executeStrategy === 'full' ? 'success' : 'warning'" size="large">
        {{ taskForm.executeStrategy === 'full' ? '全量' : '增量' }}
      </el-tag>
    </div>

    <!-- 内容区域 -->
    <el-card class="detail-card">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="任务编码">
              <span v-if="!isEdit">{{ taskForm.taskCode }}</span>
              <el-input v-else v-model="taskForm.taskCode" placeholder="请输入任务编码" />
            </el-descriptions-item>
            <el-descriptions-item label="任务分类">
              <span v-if="!isEdit">{{ taskForm.category || '-' }}</span>
              <el-input v-else v-model="taskForm.category" placeholder="请输入任务分类" />
            </el-descriptions-item>
            <el-descriptions-item label="ETL类型" :span="2">
              <span v-if="!isEdit">{{ getEtlTypeText(taskForm.etlType) }}</span>
              <el-select v-else v-model="taskForm.etlType" style="width: 200px">
                <el-option label="STG采集" value="extract" />
                <el-option label="DWD转换" value="transform" />
                <el-option label="ODS加载" value="load" />
                <el-option label="全量ETL" value="full" />
              </el-select>
            </el-descriptions-item>
            <el-descriptions-item label="执行器类型" :span="2">
              <span v-if="!isEdit">{{ getExecutorTypeText(taskForm.executorType) }}</span>
              <el-select v-else v-model="taskForm.executorType" style="width: 200px">
                <el-option label="模拟执行器" value="mock" />
                <el-option label="DataX" value="datax" />
                <el-option label="Spark SQL" value="spark" />
                <el-option label="Python脚本" value="python" />
              </el-select>
            </el-descriptions-item>
            <el-descriptions-item label="执行策略">
              <span v-if="!isEdit">{{ taskForm.executeStrategy === 'full' ? '全量' : '增量' }}</span>
              <el-radio-group v-else v-model="taskForm.executeStrategy">
                <el-radio label="full">全量</el-radio>
                <el-radio label="increment">增量</el-radio>
              </el-radio-group>
            </el-descriptions-item>
            <el-descriptions-item label="任务状态">
              <span v-if="!isEdit">{{ taskForm.status === '0' ? '启用' : '停用' }}</span>
              <el-switch v-else v-model="taskForm.status" active-value="0" inactive-value="1" />
            </el-descriptions-item>
            <el-descriptions-item label="任务描述" :span="2">
              <span v-if="!isEdit">{{ taskForm.description || '-' }}</span>
              <el-input v-else v-model="taskForm.description" type="textarea" :rows="3" />
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ taskForm.createTime }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ taskForm.updateTime }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <!-- 数据源配置 -->
        <el-tab-pane label="数据源配置" name="datasource">
          <el-form :model="taskForm" label-width="120px" :disabled="!isEdit">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="源数据源">
                  <el-select
                    v-model="taskForm.sourceDatasourceId"
                    placeholder="请选择源数据源"
                    filterable
                    style="width: 100%"
                    @change="handleSourceDatasourceChange"
                  >
                    <el-option
                      v-for="ds in datasourceList"
                      :key="ds.dataSourceId"
                      :label="ds.dataSourceName"
                      :value="ds.dataSourceId"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="目标数据源">
                  <el-select
                    v-model="taskForm.targetDatasourceId"
                    placeholder="请选择目标数据源"
                    filterable
                    style="width: 100%"
                    @change="handleTargetDatasourceChange"
                  >
                    <el-option
                      v-for="ds in datasourceList"
                      :key="ds.dataSourceId"
                      :label="ds.dataSourceName"
                      :value="ds.dataSourceId"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="源表">
                  <el-input v-model="taskForm.sourceTableName" placeholder="请输入源表名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="目标表">
                  <el-input v-model="taskForm.targetTable" placeholder="请输入目标表名" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-tab-pane>

        <!-- SQL配置 -->
        <el-tab-pane label="SQL配置" name="sql">
          <div class="sql-config">
            <div class="sql-header">
              <span>SQL配置内容</span>
              <el-button
                v-if="isEdit"
                type="primary"
                size="small"
                @click="handleFormatSQL"
              >格式化SQL</el-button>
            </div>
            <el-input
              v-model="taskForm.sqlConfig"
              type="textarea"
              :rows="20"
              placeholder="请输入SQL配置，支持采集SQL、转换SQL、加载SQL等"
              :disabled="!isEdit"
            />
          </div>
        </el-tab-pane>

        <!-- 字段映射 -->
        <el-tab-pane label="字段映射" name="mapping">
          <div class="mapping-actions">
            <el-button v-if="isEdit" type="primary" icon="Plus" @click="handleAddMapping">
              添加字段映射
            </el-button>
            <el-button v-if="isEdit" type="success" icon="MagicStick" @click="handleAutoMapping">
              自动映射
            </el-button>
            <el-button v-if="isEdit" type="warning" icon="Delete" @click="handleClearMapping">
              清空映射
            </el-button>
          </div>
          <el-table :data="fieldMappings" border stripe max-height="400">
            <el-table-column prop="sourceFieldName" label="源字段" min-width="150">
              <template #default="{ row, $index }">
                <el-input
                  v-if="isEdit"
                  v-model="row.sourceFieldName"
                  placeholder="源字段名"
                />
                <span v-else>{{ row.sourceFieldName }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="targetFieldName" label="目标字段" min-width="150">
              <template #default="{ row, $index }">
                <el-input
                  v-if="isEdit"
                  v-model="row.targetFieldName"
                  placeholder="目标字段名"
                />
                <span v-else>{{ row.targetFieldName }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="dataType" label="数据类型" width="120">
              <template #default="{ row }">
                <el-select v-if="isEdit" v-model="row.dataType" placeholder="数据类型">
                  <el-option label="STRING" value="string" />
                  <el-option label="INTEGER" value="integer" />
                  <el-option label="LONG" value="long" />
                  <el-option label="DOUBLE" value="double" />
                  <el-option label="DECIMAL" value="decimal" />
                  <el-option label="DATE" value="date" />
                  <el-option label="DATETIME" value="datetime" />
                  <el-option label="BOOLEAN" value="boolean" />
                </el-select>
                <span v-else>{{ row.dataType }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="transformRule" label="转换规则" min-width="150">
              <template #default="{ row }">
                <el-input
                  v-if="isEdit"
                  v-model="row.transformRule"
                  placeholder="转换规则"
                />
                <span v-else>{{ row.transformRule || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="isPrimaryKey" label="主键" width="80" align="center">
              <template #default="{ row }">
                <el-checkbox v-if="isEdit" v-model="row.isPrimaryKey" />
                <el-tag v-else-if="row.isPrimaryKey" type="success" size="small">是</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center" fixed="right">
              <template #default="{ $index }">
                <el-button
                  v-if="isEdit"
                  link
                  type="danger"
                  icon="Delete"
                  @click="handleDeleteMapping($index)"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 执行配置 -->
        <el-tab-pane label="执行配置" name="execution">
          <el-form :model="taskForm" label-width="150px" :disabled="!isEdit">
            <el-form-item label="执行参数配置">
              <el-input
                v-model="executorParamsJson"
                type="textarea"
                :rows="10"
                placeholder='执行参数配置（JSON格式），例如：{"concurrency": 1, "batchSize": 1000}'
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 质检规则 -->
        <el-tab-pane label="质检规则" name="quality">
          <div class="quality-actions">
            <el-button type="primary" icon="Plus" @click="handleAddQualityRule">
              添加质检规则
            </el-button>
          </div>
          <el-table :data="qualityRules" border stripe max-height="400">
            <el-table-column prop="ruleName" label="规则名称" min-width="150" />
            <el-table-column prop="ruleType" label="规则类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getQualityRuleTypeColor(row.ruleType)" size="small">
                  {{ getQualityRuleTypeText(row.ruleType) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="ruleExpression" label="规则表达式" min-width="200" show-overflow-tooltip />
            <el-table-column prop="errorMessage" label="错误提示" min-width="150" show-overflow-tooltip />
            <el-table-column prop="enabled" label="启用状态" width="100" align="center">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" @change="handleToggleQualityRule(row)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" align="center">
              <template #default="{ row }">
                <el-button link type="primary" icon="View" @click="handleViewQualityRule(row)">
                  查看
                </el-button>
                <el-button link type="danger" icon="Delete" @click="handleDeleteQualityRule(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 执行历史 -->
        <el-tab-pane label="执行历史" name="history">
          <el-table :data="executionLogs" border stripe v-loading="loadingLogs">
            <el-table-column prop="id" label="执行ID" width="80" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getExecutionStatusColor(row.status)" size="small">
                  {{ getExecutionStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="读取/写入" width="150">
              <template #default="{ row }">
                {{ formatNumber(row.rowsRead) }} / {{ formatNumber(row.rowsWritten) }}
              </template>
            </el-table-column>
            <el-table-column prop="duration" label="耗时" width="100">
              <template #default="{ row }">
                {{ formatDuration(row.duration) }}
              </template>
            </el-table-column>
            <el-table-column prop="startTime" label="开始时间" width="160" />
            <el-table-column prop="endTime" label="结束时间" width="160" />
            <el-table-column prop="executedBy" label="执行者" width="100" />
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button link type="primary" icon="View" @click="handleViewExecution(row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <pagination
            v-show="totalLogs > 0"
            :total="totalLogs"
            v-model:page="logQuery.pageNum"
            v-model:limit="logQuery.pageSize"
            @pagination="loadExecutionLogs"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 执行详情对话框 -->
    <el-dialog
      v-model="executionDetailVisible"
      title="执行详情"
      width="900px"
      append-to-body
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="执行ID">{{ currentExecution.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getExecutionStatusColor(currentExecution.status)">
            {{ getExecutionStatusText(currentExecution.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="读取行数">{{ formatNumber(currentExecution.rowsRead) }}</el-descriptions-item>
        <el-descriptions-item label="写入行数">{{ formatNumber(currentExecution.rowsWritten) }}</el-descriptions-item>
        <el-descriptions-item label="数据大小">{{ formatBytes(currentExecution.dataSize) }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ formatDuration(currentExecution.duration) }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ currentExecution.startTime }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ currentExecution.endTime }}</el-descriptions-item>
        <el-descriptions-item label="执行者">{{ currentExecution.executedBy }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2">
          <span style="color: #f56c6c">{{ currentExecution.errorMessage || '-' }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup name="ETLTaskDetail">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  VideoPlay, Edit, ArrowDown, Plus, MagicStick, Delete
} from '@element-plus/icons-vue'
import {
  getETLTask,
  addETLTask,
  updateETLTask,
  delETLTask,
  executeETLTask,
  cloneETLTask,
  validateETLConfig,
  generateDataXConfig,
  dryRunETLTask,
  listETLExecutionLog,
  getETLExecutionLogDetail,
  listETLFieldMapping,
  batchCreateFieldMapping,
  listETLQualityRule,
  delETLQualityRule
} from '@/api/data/etl'
import { listDatasource } from '@/api/data/datasource'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()

const isEdit = ref(false)
const saving = ref(false)
const loadingLogs = ref(false)
const activeTab = ref('basic')
const executionDetailVisible = ref(false)

// 使用 computed 以便实时响应路由参数变化
const taskId = computed(() => route.params.id)
const datasourceList = ref([])
const fieldMappings = ref([])
const qualityRules = ref([])
const executionLogs = ref([])
const totalLogs = ref(0)
const currentExecution = ref({})

const taskForm = reactive({
  taskName: '',
  taskCode: '',
  description: '',
  category: '',
  etlType: 'full',
  executorType: 'mock',
  executeStrategy: 'full',
  status: '0',
  sourceDatasourceId: null,
  targetDatasourceId: null,
  sourceTableName: '',
  targetTable: '',
  sqlConfig: '',
  executorParams: null
})

const executorParamsJson = computed({
  get: () => {
    return taskForm.executorParams ? JSON.stringify(taskForm.executorParams, null, 2) : '{}'
  },
  set: (value) => {
    try {
      taskForm.executorParams = JSON.parse(value)
    } catch (e) {
      console.error('JSON解析失败:', e)
    }
  }
})

const logQuery = reactive({
  pageNum: 1,
  pageSize: 10
})

onMounted(async () => {
  await loadDatasources()
  if (taskId.value !== 'new') {
    await loadTaskDetail()
    await loadFieldMappings()
    await loadQualityRules()
    await loadExecutionLogs()
  } else {
    isEdit.value = true
    if (route.query.etlType) {
      taskForm.etlType = route.query.etlType
    }
  }
})

// 监听路由变化，处理组件缓存的情况
watch(
  () => route.params.id,
  async (newId, oldId) => {
    // 只有当真正进入任务详情页时才加载（route.name 匹配）
    if (route.name !== 'ETLTaskDetail') {
      return
    }

    // 避免从新任务切换到新任务时重复加载
    if (newId === 'new' && oldId === 'new') {
      return
    }

    if (newId === 'new') {
      // 新建任务：重置表单
      Object.assign(taskForm, {
        taskName: '',
        taskCode: '',
        description: '',
        category: '',
        etlType: route.query.etlType || 'full',
        executorType: 'mock',
        executeStrategy: 'full',
        status: '0',
        sourceDatasourceId: null,
        targetDatasourceId: null,
        sourceTableName: '',
        targetTable: '',
        sqlConfig: '',
        executorParams: null
      })
      isEdit.value = true
      // 清空之前的字段映射和质检规则
      fieldMappings.value = []
      qualityRules.value = []
      executionLogs.value = []
    } else {
      console.log('进入任务详情页，加载任务ID:', newId)
      // 编辑/查看已有任务：加载数据
      isEdit.value = false
      await loadTaskDetail()
      await loadFieldMappings()
      await loadQualityRules()
      await loadExecutionLogs()
    }
  },
  { immediate: false }
)

async function loadDatasources() {
  try {
    const res = await listDatasource({ pageNum: 1, pageSize: 1000 })
    datasourceList.value = res.rows || []
  } catch (error) {
    console.error('加载数据源列表失败:', error)
  }
}

async function loadTaskDetail() {
  try {
    const res = await getETLTask(taskId.value)
    Object.assign(taskForm, res.data)
  } catch (error) {
    console.error('加载任务详情失败:', error)
  }
}

async function loadFieldMappings() {
  try {
    const res = await listETLFieldMapping({ taskId: taskId.value })
    fieldMappings.value = res.rows || []
  } catch (error) {
    console.error('加载字段映射失败:', error)
  }
}

async function loadQualityRules() {
  try {
    const res = await listETLQualityRule({ taskId: taskId.value })
    qualityRules.value = res.rows || []
  } catch (error) {
    console.error('加载质检规则失败:', error)
  }
}

async function loadExecutionLogs() {
  loadingLogs.value = true
  try {
    const res = await listETLExecutionLog({
      taskId: taskId.value,
      ...logQuery
    })
    executionLogs.value = res.rows || []
    totalLogs.value = res.total || 0
  } catch (error) {
    console.error('加载执行历史失败:', error)
  } finally {
    loadingLogs.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    let savedTaskId
    if (taskId.value === 'new') {
      const res = await addETLTask(taskForm)
      savedTaskId = res.data.id
      ElMessage.success('创建成功')
    } else {
      await updateETLTask(taskForm)
      savedTaskId = taskId.value
      ElMessage.success('保存成功')
    }

    // 保存字段映射
    if (fieldMappings.value.length > 0) {
      await batchCreateFieldMapping({
        taskId: savedTaskId,
        mappings: fieldMappings.value
      })
    }

    // 如果是新建任务，跳转到新任务详情页
    if (taskId.value === 'new') {
      router.push({
        name: 'ETLTaskDetail',
        params: { id: savedTaskId }
      })
    } else {
      isEdit.value = false
      await loadTaskDetail()
    }
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

async function handleExecute() {
  try {
    await ElMessageBox.confirm('确认要执行该任务吗？', '提示', { type: 'warning' })
    await executeETLTask(taskId.value)
    ElMessage.success('任务已提交执行')
    activeTab.value = 'history'
    await loadExecutionLogs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('执行任务失败:', error)
    }
  }
}

async function handleMoreCommand(command) {
  switch (command) {
    case 'clone':
      handleClone()
      break
    case 'validate':
      await handleValidate()
      break
    case 'datx':
      await handleGenerateDataX()
      break
    case 'dryRun':
      await handleDryRun()
      break
    case 'delete':
      await handleDelete()
      break
  }
}

async function handleClone() {
  try {
    await cloneETLTask(taskId.value, {})
    ElMessage.success('克隆成功')
  } catch (error) {
    console.error('克隆失败:', error)
  }
}

async function handleValidate() {
  try {
    await validateETLConfig(taskId.value)
    ElMessage.success('配置验证通过')
  } catch (error) {
    console.error('验证失败:', error)
  }
}

async function handleGenerateDataX() {
  try {
    const res = await generateDataXConfig(taskId.value, {})
    // 显示DataX配置JSON
    ElMessageBox.alert(JSON.stringify(res.data, null, 2), 'DataX配置', {
      customClass: 'json-dialog'
    })
  } catch (error) {
    console.error('生成配置失败:', error)
  }
}

async function handleDryRun() {
  try {
    await ElMessageBox.confirm('模拟执行不会写入目标数据，确认继续？', '提示', {
      type: 'warning'
    })
    await dryRunETLTask(taskId.value)
    ElMessage.success('模拟执行已完成')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('模拟执行失败:', error)
    }
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确认要删除该任务吗？删除后不可恢复！', '警告', {
      type: 'warning'
    })
    await delETLTask(taskId.value)
    ElMessage.success('删除成功')
    handleBack()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

function handleBack() {
  router.back()
}

function handleSourceDatasourceChange() {
  // 可以在这里加载源数据源的表列表
}

function handleTargetDatasourceChange() {
  // 可以在这里加载目标数据源的表列表
}

function handleFormatSQL() {
  // SQL格式化逻辑
}

function handleAddMapping() {
  fieldMappings.value.push({
    sourceFieldName: '',
    targetFieldName: '',
    dataType: 'string',
    transformRule: '',
    isPrimaryKey: false
  })
}

function handleDeleteMapping(index) {
  fieldMappings.value.splice(index, 1)
}

async function handleAutoMapping() {
  try {
    // 自动映射逻辑
  } catch (error) {
    console.error('自动映射失败:', error)
  }
}

function handleClearMapping() {
  fieldMappings.value = []
}

function handleAddQualityRule() {
  router.push({
    name: 'QualityRuleCreate',
    query: { taskId: taskId.value }
  })
}

async function handleToggleQualityRule(row) {
  try {
    // 切换质检规则启用状态
  } catch (error) {
    console.error('切换状态失败:', error)
  }
}

function handleViewQualityRule(row) {
  // 查看质检规则详情
}

async function handleDeleteQualityRule(row) {
  try {
    await delETLQualityRule(row.id)
    await loadQualityRules()
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('删除失败:', error)
  }
}

async function handleViewExecution(row) {
  try {
    const res = await getETLExecutionLogDetail(row.id)
    currentExecution.value = res.data
    executionDetailVisible.value = true
  } catch (error) {
    console.error('加载执行详情失败:', error)
  }
}

// 辅助函数
function getEtlTypeColor(etlType) {
  const colors = { extract: 'info', transform: 'success', load: 'warning', full: 'danger' }
  return colors[etlType] || ''
}

function getEtlTypeText(etlType) {
  const texts = { extract: 'STG采集', transform: 'DWD转换', load: 'ODS加载', full: '全量ETL' }
  return texts[etlType] || etlType
}

function getExecutorTypeText(executorType) {
  const texts = { mock: '模拟', datax: 'DataX', spark: 'Spark', python: 'Python' }
  return texts[executorType] || executorType
}

function getQualityRuleTypeText(ruleType) {
  const texts = {
    completeness: '完整性',
    accuracy: '准确性',
    consistency: '一致性',
    timeliness: '及时性',
    validity: '有效性'
  }
  return texts[ruleType] || ruleType
}

function getQualityRuleTypeColor(ruleType) {
  const colors = {
    completeness: '',
    accuracy: 'success',
    consistency: 'warning',
    timeliness: 'danger',
    validity: 'info'
  }
  return colors[ruleType] || ''
}

function getExecutionStatusText(status) {
  const texts = {
    pending: '等待执行',
    running: '执行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

function getExecutionStatusColor(status) {
  const colors = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    cancelled: ''
  }
  return colors[status] || ''
}

function formatNumber(num) {
  if (!num) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

function formatDuration(seconds) {
  if (!seconds) return '0秒'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}
</script>

<style scoped lang="scss">
.etl-task-detail {
  .page-header {
    margin-bottom: 16px;

    .header-content {
      display: flex;
      align-items: center;
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .task-status-bar {
    margin-bottom: 16px;
    display: flex;
    gap: 12px;
  }

  .detail-card {
    .mapping-actions,
    .quality-actions {
      margin-bottom: 16px;
    }

    .sql-config {
      .sql-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-weight: bold;
      }
    }
  }
}

:deep(.json-dialog) {
  .el-message-box__content {
    text-align: left;
    pre {
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }
}
</style>
