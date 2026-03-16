<template>
  <div class="task-wizard-container">
    <!-- 页面头部 -->
    <div class="wizard-header">
      <div class="header-left">
        <el-page-header @back="handleBack" :content="pageTitle">
          <template #extra>
            <div class="header-actions">
              <el-button v-if="taskId" :icon="Clock" @click="handleShowVersions">
                版本管理
              </el-button>
              <el-button :icon="View" @click="handlePreviewConfig">
                预览配置
              </el-button>
            </div>
          </template>
        </el-page-header>
      </div>
      <div class="header-right">
        <el-button @click="handleBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveDraft">
          保存草稿
        </el-button>
        <el-button
          v-if="currentStep === totalSteps - 1"
          type="success"
          :loading="publishing"
          @click="handlePublish"
        >
          <el-icon><VideoPlay /></el-icon>
          {{ isEdit ? '保存并发布' : '创建任务' }}
        </el-button>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="wizard-main">
      <!-- 左侧步骤导航 -->
      <div class="wizard-sidebar">
        <el-steps
          :active="currentStep"
          direction="vertical"
          process-status="process"
          finish-status="success"
        >
          <el-step
            v-for="(step, index) in steps"
            :key="index"
            :title="step.title"
            :description="step.description"
            :icon="step.icon"
            @click="handleStepClick(index)"
            :class="{ 'step-clickable': canClickStep(index) }"
          />
        </el-steps>

        <!-- 配置完成度 -->
        <div class="completion-status">
          <el-progress
            type="circle"
            :percentage="completionPercentage"
            :width="100"
            :stroke-width="8"
          >
            <template #default="{ percentage }">
              <span class="percentage-value">{{ percentage }}%</span>
              <span class="percentage-label">完成度</span>
            </template>
          </el-progress>
        </div>
      </div>

      <!-- 右侧表单内容 -->
      <div class="wizard-content">
        <el-card shadow="never" class="content-card">
          <!-- 步骤1: 基本信息 -->
          <div v-show="currentStep === 0" class="step-content">
            <BasicInfoStep
              ref="basicInfoStepRef"
              v-model="formData"
              :is-edit="isEdit"
              @change="handleStepDataChange(0, $event)"
            />
          </div>

          <!-- 步骤2: 源端配置 -->
          <div v-show="currentStep === 1" class="step-content">
            <SourceStep
              ref="sourceStepRef"
              v-model="formData"
              :datasource-options="datasourceOptions"
              @change="handleStepDataChange(1, $event)"
              @datasource-change="handleSourceDatasourceChange"
            />
          </div>

          <!-- 步骤3: 转换/映射 -->
          <div v-show="currentStep === 2" class="step-content">
            <TransformStep
              ref="transformStepRef"
              v-model="formData"
              :etl-type="formData.etlType"
              @change="handleStepDataChange(2, $event)"
            />
          </div>

          <!-- 步骤4: 目标端配置 -->
          <div v-show="currentStep === 3" class="step-content">
            <TargetStep
              ref="targetStepRef"
              v-model="formData"
              :datasource-options="datasourceOptions"
              @change="handleStepDataChange(3, $event)"
            />
          </div>

          <!-- 步骤5: 高级与调度配置 -->
          <div v-show="currentStep === 4" class="step-content">
            <AdvancedStep
              ref="advancedStepRef"
              v-model="formData"
              @change="handleStepDataChange(4, $event)"
            />
          </div>

          <!-- 步骤导航按钮 -->
          <div class="step-actions">
            <el-button v-if="currentStep > 0" @click="handlePrevStep">
              <el-icon><ArrowLeft /></el-icon>
              上一步
            </el-button>
            <el-button
              v-if="currentStep < totalSteps - 1"
              type="primary"
              @click="handleNextStep"
            >
              下一步
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 配置预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="配置预览"
      width="900px"
      append-to-body
    >
      <ConfigPreview :config="formData" :etl-type="formData.etlType" />
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleCopyConfig">复制配置JSON</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="ETLTaskDetail">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ArrowLeft,
  ArrowRight,
  VideoPlay,
  Clock,
  View
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getETLTask,
  addETLTask,
  updateETLTask
} from '@/api/data/etl'
import {
  listDatasource
} from '@/api/data/asset'
import BasicInfoStep from './steps/BasicInfoStep.vue'
import SourceStep from './steps/SourceStep.vue'
import TransformStep from './steps/TransformStep.vue'
import TargetStep from './steps/TargetStep.vue'
import AdvancedStep from './steps/AdvancedStep.vue'
import ConfigPreview from './components/ConfigPreview.vue'

const router = useRouter()
const route = useRoute()

// 步骤定义
const steps = ref([
  {
    title: '基本信息',
    description: '配置任务名称、类型和业务域',
    icon: 'Document'
  },
  {
    title: '源端配置',
    description: '选择数据源和抽取方式',
    icon: 'Connection'
  },
  {
    title: '转换映射',
    description: '配置字段映射或SQL脚本',
    icon: 'Operation'
  },
  {
    title: '目标端配置',
    description: '配置目标表和写入方式',
    icon: 'Upload'
  },
  {
    title: '高级配置',
    description: '调度策略、资源申请和失败重试',
    icon: 'Setting'
  }
])

// 状态管理
const currentStep = ref(0)
const totalSteps = computed(() => steps.value.length)
const isEdit = computed(() => !!taskId.value)
const taskId = ref(route.params.id || '')
const saving = ref(false)
const publishing = ref(false)
const previewDialogVisible = ref(false)

// 步骤组件引用
const basicInfoStepRef = ref()
const sourceStepRef = ref()
const transformStepRef = ref()
const targetStepRef = ref()
const advancedStepRef = ref()

// 数据源选项
const datasourceOptions = ref([])

// 表单数据
const formData = reactive({
  // 基本信息
  taskName: '',
  taskCode: '',
  etlType: 'data_integration',
  businessDomain: '',
  priority: 'medium',
  description: '',
  status: '0',

  // 源端配置
  sourceDatasourceId: '',
  sourceDatabase: '',
  sourceTableName: '',
  sourceQueryType: 'table', // table 或 query
  sourceQuery: '',
  extractMode: 'full', // full 或 increment
  incrementField: '',
  incrementStrategy: 'timestamp', // timestamp 或 auto_increment

  // 转换/映射配置
  fieldMappings: [],
  sourceColumns: [],
  targetColumns: [],
  sqlScript: '',
  transformRules: '',

  // 目标端配置
  targetDatasourceId: '',
  targetDatabase: '',
  targetTableName: '',
  writeMode: 'append', // append, overwrite, upsert
  partitionFields: [],
  preSql: '',
  postSql: '',

  // 高级配置
  executorType: 'datax',
  scheduleType: 'manual', // manual 或 cron
  scheduleCron: '0 0 * * *',
  scheduleDescription: '',
  executorMemory: '2g',
  executorCores: 2,
  executorInstances: 2,
  retryTimes: 3,
  retryInterval: 60,
  timeout: 300,

  // 多租户配置
  multiTenant: {
    enabled: false,
    tenantIdField: '',
    tenantId: '',
    tenantSourceIds: []
  },

  // 其他
  remark: ''
})

// 步骤验证状态
const stepValidationStatus = ref([false, false, false, false, false])

// 计算属性
const pageTitle = computed(() => {
  return isEdit.value ? '编辑ETL任务' : '创建ETL任务'
})

const completionPercentage = computed(() => {
  const completed = stepValidationStatus.value.filter(status => status).length
  return Math.round((completed / totalSteps.value) * 100)
})

// 生命周期
onMounted(() => {
  loadDatasources()
  if (isEdit.value) {
    loadTaskDetail()
  } else {
    initDefaultData()
  }
})

// 方法
async function loadDatasources() {
  try {
    const res = await listDatasource({ pageNum: 1, pageSize: 1000 })
    datasourceOptions.value = res.rows || []
  } catch (error) {
    console.error('加载数据源失败:', error)
  }
}

async function loadTaskDetail() {
  try {
    const res = await getETLTask(taskId.value)
    Object.assign(formData, res.data)
  } catch (error) {
    ElMessage.error('加载任务详情失败')
  }
}

function initDefaultData() {
  formData.taskCode = generateTaskCode()
  formData.executorType = formData.etlType === 'data_integration' ? 'datax' : 'spark'
}

function generateTaskCode() {
  const timestamp = Date.now().toString(36).toUpperCase()
  return `ETL_${timestamp}`
}

function handleBack() {
  router.back()
}

function handleStepClick(index) {
  if (canClickStep(index)) {
    currentStep.value = index
  }
}

function canClickStep(index) {
  // 只能点击已验证过的步骤或当前步骤的下一步
  if (index <= currentStep.value) return true
  if (index === currentStep.value + 1) {
    return stepValidationStatus.value[currentStep.value]
  }
  return false
}

async function handleNextStep() {
  const currentRef = getStepRef(currentStep.value)
  if (currentRef) {
    try {
      const valid = await currentRef.validate()
      if (valid) {
        stepValidationStatus.value[currentStep.value] = true
        if (currentStep.value < totalSteps.value - 1) {
          currentStep.value++
        }
      }
    } catch (error) {
      ElMessage.error('请完成当前步骤的必填项')
    }
  }
}

function handlePrevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function getStepRef(stepIndex) {
  const refs = [
    basicInfoStepRef,
    sourceStepRef,
    transformStepRef,
    targetStepRef,
    advancedStepRef
  ]
  return refs[stepIndex]?.value
}

function handleStepDataChange(stepIndex, data) {
  stepValidationStatus.value[stepIndex] = data.valid || false
}

function handleSourceDatasourceChange(datasourceId) {
  // 数据源变更时，清空相关配置
  formData.sourceDatabase = ''
  formData.sourceTableName = ''
  formData.sourceColumns = []
  formData.fieldMappings = []
}

async function handleSaveDraft() {
  saving.value = true
  try {
    const data = buildSubmitData()
    if (isEdit.value) {
      await updateETLTask(data)
      ElMessage.success('保存成功')
    } else {
      const res = await addETLTask(data)
      taskId.value = res.data.taskId
      ElMessage.success('草稿保存成功')
    }
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handlePublish() {
  // 验证所有步骤
  for (let i = 0; i < totalSteps.value; i++) {
    const ref = getStepRef(i)
    if (ref) {
      try {
        await ref.validate()
      } catch (error) {
        currentStep.value = i
        ElMessage.error(`请完成"${steps.value[i].title}"步骤的必填项`)
        return
      }
    }
  }

  publishing.value = true
  try {
    const data = buildSubmitData()
    data.status = '0' // 启用状态

    if (isEdit.value) {
      await updateETLTask(data)
      ElMessage.success('任务更新成功')
    } else {
      const res = await addETLTask(data)
      taskId.value = res.data.taskId
      ElMessage.success('任务创建成功')
    }

    // 询问是否立即执行
    await ElMessageBox.confirm(
      '任务已创建成功，是否立即执行？',
      '提示',
      {
        confirmButtonText: '立即执行',
        cancelButtonText: '返回列表',
        type: 'success'
      }
    )

    // 跳转到执行页面
    router.push(`/data-etl/execution?taskId=${taskId.value}`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  } finally {
    publishing.value = false
  }
}

function buildSubmitData() {
  return {
    taskId: taskId.value,
    ...formData,
    executorParams: buildExecutorParams()
  }
}

function buildExecutorParams() {
  const params = {
    timeout: formData.timeout,
    retryTimes: formData.retryTimes
  }

  if (formData.etlType === 'data_integration' && formData.executorType === 'datax') {
    params.datax = {
      reader: {
        column: formData.sourceColumns,
        querySql: formData.sourceQueryType === 'query' ? formData.sourceQuery : ''
      },
      writer: {
        writeMode: formData.writeMode,
        preSql: formData.preSql,
        postSql: formData.postSql
      },
      speed: {
        channel: formData.executorInstances,
        byte: formData.executorMemory === '2g' ? 1048576 : formData.executorMemory === '4g' ? 2097152 : 4194304,
        record: 100000
      }
    }
    params.incremental = {
      enabled: formData.extractMode === 'increment',
      field: formData.incrementField,
      strategy: formData.incrementStrategy
    }
    params.multi_tenant = formData.multiTenant
  } else if (formData.etlType === 'sql_task' && formData.executorType === 'spark') {
    params.spark = {
      sql: formData.sqlScript,
      appName: formData.taskName,
      executorMemory: formData.executorMemory,
      executorCores: formData.executorCores,
      executorInstances: formData.executorInstances
    }
  }

  return params
}

function handlePreviewConfig() {
  previewDialogVisible.value = true
}

function handleCopyConfig() {
  const config = JSON.stringify(buildSubmitData(), null, 2)
  navigator.clipboard.writeText(config).then(() => {
    ElMessage.success('配置已复制到剪贴板')
  })
}

function handleShowVersions() {
  router.push(`/data-etl/task/versions/${taskId.value}`)
}
</script>

<style scoped lang="scss">
.task-wizard-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.wizard-header {
  background: #fff;
  padding: 16px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10;

  .header-left {
    flex: 1;
  }

  .header-actions {
    display: flex;
    gap: 8px;
  }

  .header-right {
    display: flex;
    gap: 12px;
  }
}

.wizard-main {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 24px;
  gap: 24px;
}

.wizard-sidebar {
  width: 320px;
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;

  :deep(.el-steps) {
    flex: 1;
  }

  :deep(.el-step) {
    cursor: default;
  }

  :deep(.step-clickable) {
    cursor: pointer;

    .el-step__title {
      color: #409EFF;
    }
  }

  .completion-status {
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #ebeef5;
    text-align: center;

    .percentage-value {
      display: block;
      font-size: 24px;
      font-weight: bold;
      color: #409EFF;
    }

    .percentage-label {
      display: block;
      font-size: 12px;
      color: #909399;
      margin-top: 4px;
    }
  }
}

.wizard-content {
  flex: 1;
  overflow: hidden;

  .content-card {
    height: 100%;
    display: flex;
    flex-direction: column;

    :deep(.el-card__body) {
      flex: 1;
      overflow-y: auto;
      padding: 32px;
    }
  }
}

.step-content {
  min-height: 100%;
}

.step-actions {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: center;
  gap: 16px;
}

:deep(.el-page-header) {
  .el-page-header__content {
    font-size: 18px;
    font-weight: 500;
  }
}

:deep(.el-step__description) {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
