<template>
  <div class="simplified-wizard">
    <!-- 步骤指示器 -->
    <div class="wizard-header">
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step
          v-for="(title, index) in stepTitles"
          :key="index"
          :title="title"
          :description="stepDescriptions[index]"
        />
      </el-steps>
    </div>

    <!-- 步骤内容 -->
    <div class="wizard-content">
      <!-- 步骤1: 数据源选择（使用场景组件） -->
      <transition name="fade" mode="out-in">
        <div v-if="currentStep === 0" key="step1" class="step-panel">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <span class="header-title">{{ stepTitles[0] }}</span>
                <el-tag v-if="scenarioLabel" type="info">{{ scenarioLabel }}</el-tag>
              </div>
            </template>

            <!-- 动态场景组件 -->
            <component
              :is="currentScenarioComponent"
              v-model="formData"
              ref="scenarioFormRef"
              @source-change="handleSourceChange"
              @source-table-change="handleSourceTableChange"
              @target-change="handleTargetChange"
              @show-sql-help="showSqlHelp"
            />
          </el-card>
        </div>

        <!-- 步骤2: 字段映射 -->
        <div v-else-if="currentStep === 1" key="step2" class="step-panel">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <span class="header-title">{{ stepTitles[1] }}</span>
                <el-button type="primary" plain size="small" @click="autoMapFields">
                  <el-icon><MagicStick /></el-icon>
                  智能映射
                </el-button>
              </div>
            </template>

            <!-- 字段映射编辑器 -->
            <field-mapping
              v-model:source-columns="formData.sourceColumns"
              v-model:target-columns="formData.targetColumns"
              v-model:mappings="formData.fieldMappings"
              :auto-match="false"
            />

            <!-- 数据预览 -->
            <el-divider content-position="left">数据预览（前10条）</el-divider>
            <data-preview
              v-if="showPreview"
              :source-config="previewConfig"
              :loading="previewLoading"
            />
            <el-empty v-else description="请先完成数据源配置" />
          </el-card>
        </div>

        <!-- 步骤3: 执行设置 -->
        <div v-else-if="currentStep === 2" key="step3" class="step-panel">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <span class="header-title">{{ stepTitles[2] }}</span>
              </div>
            </template>

            <el-form :model="formData" :rules="step3Rules" ref="step3FormRef" label-width="140px">
              <!-- 同步方式 -->
              <el-form-item label="同步方式">
                <el-radio-group v-model="formData.syncMode" @change="handleSyncModeChange">
                  <el-radio label="full">
                    <div class="radio-content">
                      <div class="radio-title">全量同步</div>
                      <div class="radio-desc">每次同步全部数据，适合小表或初始化</div>
                    </div>
                  </el-radio>
                  <el-radio label="incremental">
                    <div class="radio-content">
                      <div class="radio-title">增量同步</div>
                      <div class="radio-desc">只同步新增或变更的数据，更高效</div>
                    </div>
                  </el-radio>
                </el-radio-group>
              </el-form-item>

              <!-- 增量字段 -->
              <el-form-item v-if="formData.syncMode === 'incremental'" label="增量标识字段" prop="incrementalField">
                <el-select v-model="formData.incrementalField" filterable placeholder="请选择增量字段" style="width: 100%">
                  <el-option
                    v-for="col in formData.sourceColumns"
                    :key="col"
                    :label="col"
                    :value="col"
                  >
                    <span>{{ col }}</span>
                    <span style="color: #8492a6; font-size: 12px; margin-left: 8px">
                      {{ getFieldTypeHint(col) }}
                    </span>
                  </el-option>
                </el-select>
                <div class="form-tip">
                  <el-tooltip content="用于判断哪些数据是新增的，通常是时间戳或自增ID字段" placement="top">
                    <el-icon><QuestionFilled /></el-icon>
                  </el-tooltip>
                  系统会记录上次同步的值，只同步大于该值的数据
                </div>
              </el-form-item>

              <!-- 任务名称 -->
              <el-form-item label="任务名称" prop="taskName">
                <el-input
                  v-model="formData.taskName"
                  placeholder="自动生成，可修改"
                  clearable
                >
                  <template #append>
                    <el-button @click="generateTaskName" :icon="Refresh" />
                  </template>
                </el-input>
              </el-form-item>

              <!-- 执行方式 -->
              <el-form-item label="执行方式">
                <el-radio-group v-model="formData.scheduleType">
                  <el-radio label="manual">
                    <div class="radio-content">
                      <div class="radio-title">立即执行</div>
                      <div class="radio-desc">保存后立即开始同步</div>
                    </div>
                  </el-radio>
                  <el-radio label="scheduled">
                    <div class="radio-content">
                      <div class="radio-title">定时执行</div>
                      <div class="radio-desc">按照设定的时间周期自动执行</div>
                    </div>
                  </el-radio>
                </el-radio-group>
              </el-form-item>

              <!-- 定时配置 -->
              <template v-if="formData.scheduleType === 'scheduled'">
                <el-form-item label="执行周期" prop="scheduleCron">
                  <schedule-select v-model="formData.scheduleCron" style="width: 100%" />
                </el-form-item>
              </template>

              <!-- 高级选项 -->
              <el-collapse style="margin-top: 16px">
                <el-collapse-item name="advanced">
                  <template #title>
                    <span style="color: #909399">
                      <el-icon><Setting /></el-icon>
                      高级选项（通常不需要修改）
                    </span>
                  </template>
                  <el-form-item label="执行器类型">
                    <el-select v-model="formData.executorType" disabled style="width: 100%">
                      <el-option label="DataX（推荐）" value="datax" />
                      <el-option label="Spark SQL" value="spark_sql" />
                    </el-select>
                    <div class="form-tip">已根据场景自动选择最佳执行器</div>
                  </el-form-item>
                  <el-form-item label="批处理大小">
                    <el-input-number
                      v-model="formData.batchSize"
                      :min="1000"
                      :max="100000"
                      :step="1000"
                      style="width: 200px"
                    />
                    <span style="margin-left: 12px; color: #909399; font-size: 12px">行/批次</span>
                  </el-form-item>
                  <el-form-item label="并发数">
                    <el-input-number
                      v-model="formData.concurrency"
                      :min="1"
                      :max="10"
                      style="width: 200px"
                    />
                    <span style="margin-left: 12px; color: #909399; font-size: 12px">同时处理的任务数</span>
                  </el-form-item>
                </el-collapse-item>
              </el-collapse>
            </el-form>

            <!-- 配置摘要 -->
            <el-divider content-position="left">配置摘要</el-divider>
            <config-summary :config="formData" :scenario="scenario" />
          </el-card>
        </div>
      </transition>
    </div>

    <!-- 底部操作栏 -->
    <div class="wizard-footer">
      <el-button v-if="currentStep > 0" @click="prevStep">
        <el-icon><ArrowLeft /></el-icon>
        上一步
      </el-button>
      <el-button v-if="currentStep < 2" type="primary" @click="nextStep">
        下一步
        <el-icon><ArrowRight /></el-icon>
      </el-button>
      <el-button
        v-if="currentStep === 2"
        type="success"
        :loading="submitting"
        @click="submitWizard"
      >
        <el-icon><VideoPlay /></el-icon>
        {{ formData.scheduleType === 'manual' ? '保存并立即执行' : '保存任务' }}
      </el-button>
      <el-button @click="handleCancel">取消</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import {
  ArrowLeft, ArrowRight, VideoPlay, MagicStick, QuestionFilled, Refresh, Setting
} from '@element-plus/icons-vue'
import FieldMapping from '@/components/FieldMapping'
import DataPreview from './DataPreview'
import ConfigSummary from './ConfigSummary'
import ScheduleSelect from './ScheduleSelect'
import { SCENARIO_CONFIGS } from './scenarioConfig'
import { getScenarioComponent, getScenarioInfo } from './scenarios'

const props = defineProps({
  scenario: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['submit', 'cancel'])

const currentStep = ref(0)
const submitting = ref(false)
const showPreview = ref(false)
const previewLoading = ref(false)

const scenarioFormRef = ref()
const step3FormRef = ref()

const formData = reactive({
  // 基础字段
  sourceDatasourceId: '',
  sourceTable: '',
  targetDatasourceId: '',
  targetTable: '',
  whereCondition: '',
  transformRules: '',
  sqlScript: '',
  targetLayer: 'dwd',
  writeMode: 'overwrite',

  // 字段相关
  sourceColumns: [],
  targetColumns: [],
  fieldMappings: [],

  // 同步配置
  syncMode: 'full',
  incrementalField: '',

  // 任务信息
  taskName: '',
  scheduleType: 'manual',
  scheduleCron: '0 0 * * *',

  // 高级配置
  executorType: 'datax',
  batchSize: 10000,
  concurrency: 1
})

// 当前场景组件
const currentScenarioComponent = computed(() => {
  return getScenarioComponent(props.scenario)
})

// 场景信息
const scenarioInfo = computed(() => {
  return getScenarioInfo(props.scenario)
})

// 步骤标题和描述
const stepTitles = computed(() => {
  return scenarioInfo.value?.steps || ['选择数据源', '配置映射', '执行设置']
})

const stepDescriptions = computed(() => {
  const descriptions = {
    biz_to_stg: ['选择要同步的业务库和表', '设置源表和目标表的字段对应关系', '选择全量或增量同步'],
    stg_to_ods: ['选择STG层的表', '配置数据清洗规则和字段映射', '选择全量或增量同步'],
    warehouse_transform: ['编写Spark SQL脚本', '配置输出字段映射', '设置任务执行计划'],
    warehouse_to_biz: ['选择数仓表和目标业务库', '设置字段映射关系', '选择立即或定时执行'],
    db_to_db: ['选择源库和目标库', '配置字段映射关系', '选择全量或增量同步']
  }
  return descriptions[props.scenario] || ['', '', '']
})

const scenarioLabel = computed(() => {
  return scenarioInfo.value?.name || ''
})

// 预览配置
const previewConfig = computed(() => ({
  datasourceId: formData.sourceDatasourceId,
  table: formData.sourceTable,
  where: formData.whereCondition
}))

// 表单验证规则
const step3Rules = {
  taskName: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  incrementalField: [{ required: true, message: '请选择增量字段', trigger: 'change' }]
}

// 初始化配置
onMounted(() => {
  const scenarioConfig = SCENARIO_CONFIGS[props.scenario] || {}
  Object.assign(formData, scenarioConfig.defaults || {})
  formData.executorType = scenarioConfig.executorType || 'datax'
  generateTaskName()
})

// 事件处理
function handleSourceChange() {
  formData.sourceTable = ''
  formData.sourceColumns = []
  formData.fieldMappings = []
  showPreview.value = false
}

function handleSourceTableChange() {
  loadSourceColumns()
  if (props.scenario !== 'warehouse_transform') {
    autoGenerateTargetTable()
  }
}

function handleTargetChange() {
  formData.targetTable = ''
  formData.targetColumns = []
}

function handleSyncModeChange() {
  if (formData.syncMode === 'full') {
    formData.incrementalField = ''
  }
}

async function loadSourceColumns() {
  // TODO: 调用API获取源表字段
  // 这里需要根据具体的数据源类型调用不同的API
}

function autoGenerateTargetTable() {
  if (formData.sourceTable && !formData.targetTable) {
    formData.targetTable = formData.sourceTable
  }
}

function autoMapFields() {
  if (formData.sourceColumns.length === 0) {
    return
  }

  const mappings = []
  const sourceMapping = new Map(formData.sourceColumns.map(col => [col.toLowerCase(), col]))

  // 精确匹配
  formData.targetColumns.forEach(targetCol => {
    const targetLower = targetCol.toLowerCase()
    if (sourceMapping.has(targetLower)) {
      mappings.push({
        source: sourceMapping.get(targetLower),
        target: targetCol
      })
    }
  })

  formData.fieldMappings = mappings
}

function generateTaskName() {
  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const table = formData.sourceTable || 'table'
  const scenarioName = scenarioInfo.value?.name || '数据同步'
  formData.taskName = `${scenarioName}_${table}_${timestamp}`
}

function getFieldTypeHint(fieldName) {
  const lower = fieldName.toLowerCase()
  if (lower.includes('time') || lower.includes('date')) {
    return '适合作为时间增量字段'
  } else if (lower === 'id' || lower.includes('_id')) {
    return '适合作为ID增量字段'
  }
  return ''
}

async function nextStep() {
  if (currentStep.value === 0) {
    const valid = await scenarioFormRef.value?.validate().catch(() => false)
    if (!valid) return

    // 如果是数仓计算场景，跳过字段映射步骤
    if (scenarioInfo.value?.skipMapping) {
      currentStep.value = 2
      return
    }
  }

  if (currentStep.value === 1 && formData.fieldMappings.length === 0) {
    autoMapFields()
  }

  currentStep.value++
}

function prevStep() {
  if (currentStep.value === 2 && scenarioInfo.value?.skipMapping) {
    currentStep.value = 0
  } else {
    currentStep.value--
  }
}

async function submitWizard() {
  const valid = await step3FormRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true

  try {
    const submitData = buildSubmitData()
    emit('submit', submitData)
  } finally {
    submitting.value = false
  }
}

function buildSubmitData() {
  const scenarioConfig = SCENARIO_CONFIGS[props.scenario] || {}

  return {
    scenario: props.scenario,
    taskName: formData.taskName,
    taskType: scenarioConfig.taskType,
    targetLayer: formData.targetLayer || scenarioConfig.targetLayer,
    executorType: formData.executorType,
    syncMode: formData.syncMode,
    incrementalField: formData.incrementalField,
    scheduleType: formData.scheduleType,
    scheduleCron: formData.scheduleCron,
    batchSize: formData.batchSize,
    concurrency: formData.concurrency,
    detail: {
      source: {
        datasourceId: formData.sourceDatasourceId,
        table: formData.sourceTable,
        database: formData.sourceDatabase,
        where: formData.whereCondition
      },
      target: {
        datasourceId: formData.targetDatasourceId,
        table: formData.targetTable,
        database: formData.targetDatabase,
        writeMode: formData.writeMode
      },
      sourceColumns: formData.sourceColumns,
      targetColumns: formData.targetColumns,
      fieldMappings: formData.fieldMappings,
      transformRules: formData.transformRules,
      sqlScript: formData.sqlScript
    }
  }
}

function handleCancel() {
  emit('cancel')
}

function showSqlHelp() {
  // 打开SQL帮助对话框
}
</script>

<style scoped>
.simplified-wizard {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.wizard-header {
  margin-bottom: 32px;
  padding: 0 40px;
}

.wizard-content {
  min-height: 500px;
}

.step-panel {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.radio-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.radio-title {
  font-weight: 500;
  color: #303133;
}

.radio-desc {
  font-size: 12px;
  color: #909399;
}

.wizard-footer {
  margin-top: 32px;
  padding: 16px;
  background: #fff;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: center;
  gap: 12px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
