<template>
  <div class="advanced-step">
    <el-alert
      title="高级配置"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 24px"
    >
      配置任务调度策略、资源申请、失败重试等高级参数
    </el-alert>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="160px"
      label-position="right"
    >
      <!-- 调度配置 -->
      <el-card shadow="never" class="config-section">
        <template #header>
          <div class="card-header">
            <el-icon><Clock /></el-icon>
            <span>调度配置</span>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="执行方式" prop="scheduleType">
              <el-radio-group v-model="formData.scheduleType" @change="handleScheduleTypeChange">
                <el-radio label="manual">
                  <div class="radio-content">
                    <div class="radio-title">手动执行</div>
                    <div class="radio-desc">保存后需要手动触发执行</div>
                  </div>
                </el-radio>
                <el-radio label="scheduled">
                  <div class="radio-content">
                    <div class="radio-title">定时调度</div>
                    <div class="radio-desc">按照Cron表达式周期性自动执行</div>
                  </div>
                </el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- Cron表达式配置 -->
        <template v-if="formData.scheduleType === 'scheduled'">
          <el-row :gutter="24">
            <el-col :span="24">
              <el-form-item label="Cron表达式" prop="scheduleCron">
                <ScheduleSelect
                  v-model="formData.scheduleCron"
                  style="width: 100%"
                />
                <div class="form-tip">
                  <el-icon><QuestionFilled /></el-icon>
                  配置任务的执行周期，支持秒、分、时、日、月、周等维度
                </div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="24">
              <el-form-item label="调度说明">
                <el-input
                  v-model="formData.scheduleDescription"
                  type="textarea"
                  :rows="2"
                  placeholder="例如：每天凌晨2点执行，用于同步前一天的业务数据"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
      </el-card>

      <!-- 资源配置 -->
      <el-card shadow="never" class="config-section">
        <template #header>
          <div class="card-header">
            <el-icon><Cpu /></el-icon>
            <span>资源配置</span>
            <el-tag size="small" type="info">根据数据量调整</el-tag>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :span="8">
            <el-form-item label="执行器内存">
              <el-select
                v-model="formData.executorMemory"
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option label="2GB" value="2g" />
                <el-option label="4GB" value="4g" />
                <el-option label="8GB" value="8g" />
                <el-option label="16GB" value="16g" />
              </el-select>
              <div class="form-tip">每个执行器的内存大小</div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="CPU核心数">
              <el-input-number
                v-model="formData.executorCores"
                :min="1"
                :max="8"
                :step="1"
                style="width: 100%"
              />
              <div class="form-tip">每个执行器的CPU核心数</div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="执行器实例数">
              <el-input-number
                v-model="formData.executorInstances"
                :min="1"
                :max="10"
                :step="1"
                style="width: 100%"
              />
              <div class="form-tip">并发执行的执行器数量</div>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 资源预估 -->
        <el-row :gutter="24">
          <el-col :span="24">
            <el-alert
              :title="`预计资源使用：${totalMemory}GB 内存 × ${formData.executorInstances} 实例 = ${totalMemory * formData.executorInstances}GB 总内存`"
              type="success"
              :closable="false"
              show-icon
            >
              <template #default>
                <div>总CPU核心：{{ formData.executorCores * formData.executorInstances }} 核</div>
              </template>
            </el-alert>
          </el-col>
        </el-row>
      </el-card>

      <!-- 失败重试配置 -->
      <el-card shadow="never" class="config-section">
        <template #header>
          <div class="card-header">
            <el-icon><RefreshRight /></el-icon>
            <span>失败重试</span>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="重试次数" prop="retryTimes">
              <el-input-number
                v-model="formData.retryTimes"
                :min="0"
                :max="5"
                :step="1"
                style="width: 100%"
              />
              <div class="form-tip">任务失败后的最大重试次数</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="重试间隔（秒）" prop="retryInterval">
              <el-input-number
                v-model="formData.retryInterval"
                :min="30"
                :max="600"
                :step="30"
                style="width: 100%"
              />
              <div class="form-tip">每次重试之间的等待时间</div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="超时时间（秒）" prop="timeout">
              <el-input-number
                v-model="formData.timeout"
                :min="60"
                :max="7200"
                :step="60"
                style="width: 200px"
              />
              <span style="margin-left: 12px; color: #909399; font-size: 12px">
                任务执行超时时间，超时后将自动取消
              </span>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 依赖配置 -->
      <el-card shadow="never" class="config-section">
        <template #header>
          <div class="card-header">
            <el-icon><Link /></el-icon>
            <span>任务依赖</span>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="依赖任务">
              <el-select
                v-model="formData.dependentTasks"
                multiple
                filterable
                remote
                reserve-keyword
                placeholder="搜索并选择依赖的任务"
                :remote-method="searchDependentTasks"
                :loading="loadingDependentTasks"
                style="width: 100%"
              >
                <el-option
                  v-for="task in dependentTaskOptions"
                  :key="task.id"
                  :label="task.name"
                  :value="task.id"
                >
                  <div class="task-option">
                    <span class="task-name">{{ task.name }}</span>
                    <el-tag size="small">{{ task.type }}</el-tag>
                  </div>
                </el-option>
              </el-select>
              <div class="form-tip">
                <el-icon><QuestionFilled /></el-icon>
                当前任务将在所选依赖任务成功执行后才开始执行
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="依赖策略">
              <el-select
                v-model="formData.dependencyStrategy"
                placeholder="请选择依赖策略"
                style="width: 100%"
              >
                <el-option label="全部成功" value="all_success">
                  <div class="option-content">
                    <span>所有依赖任务都成功后才执行</span>
                    <span class="option-desc">最严格，确保所有前置数据都就绪</span>
                  </div>
                </el-option>
                <el-option label="任一成功" value="any_success">
                  <div class="option-content">
                    <span>任一依赖任务成功即执行</span>
                    <span class="option-desc">适合有多个数据源的场景</span>
                  </div>
                </el-option>
                <el-option label="全部完成" value="all_finished">
                  <div class="option-content">
                    <span>所有依赖任务完成即执行</span>
                    <span class="option-desc">不管成功失败，完成就执行</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="等待超时（分钟）">
              <el-input-number
                v-model="formData.dependencyTimeout"
                :min="0"
                :max="1440"
                :step="10"
                style="width: 100%"
              />
              <div class="form-tip">0表示永久等待</div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 告警配置 -->
      <el-card shadow="never" class="config-section">
        <template #header>
          <div class="card-header">
            <el-icon><Bell /></el-icon>
            <span>告警通知</span>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="告警方式">
              <el-checkbox-group v-model="formData.alertTypes">
                <el-checkbox label="email">
                  <div class="checkbox-content">
                    <span>邮件通知</span>
                    <span class="checkbox-desc">发送邮件到指定邮箱</span>
                  </div>
                </el-checkbox>
                <el-checkbox label="sms">
                  <div class="checkbox-content">
                    <span>短信通知</span>
                    <span class="checkbox-desc">发送短信到手机</span>
                  </div>
                </el-checkbox>
                <el-checkbox label="webhook">
                  <div class="checkbox-content">
                    <span>Webhook</span>
                    <span class="checkbox-desc">调用自定义接口</span>
                  </div>
                </el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
        </el-row>

        <template v-if="formData.alertTypes.includes('webhook')">
          <el-row :gutter="24">
            <el-col :span="24">
              <el-form-item label="Webhook地址">
                <el-input
                  v-model="formData.webhookUrl"
                  placeholder="请输入Webhook地址"
                  clearable
                />
                <div class="form-tip">
                  <el-icon><QuestionFilled /></el-icon>
                  支持钉钉、企业微信、飞书等机器人webhook
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="告警时机">
              <el-checkbox-group v-model="formData.alertTriggers">
                <el-checkbox label="failure">任务失败时</el-checkbox>
                <el-checkbox label="success">任务成功时</el-checkbox>
                <el-checkbox label="timeout">任务超时时</el-checkbox>
                <el-checkbox label="retry">重试失败时</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="通知对象">
              <el-select
                v-model="formData.alertRecipients"
                multiple
                filterable
                allow-create
                placeholder="请输入邮箱或手机号"
                style="width: 100%"
              >
                <el-option
                  v-for="recipient in commonRecipients"
                  :key="recipient"
                  :label="recipient"
                  :value="recipient"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  Clock,
  Cpu,
  RefreshRight,
  Link,
  Bell,
  QuestionFilled
} from '@element-plus/icons-vue'
import ScheduleSelect from '../components/ScheduleSelect.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const formRef = ref()
const dependentTaskOptions = ref([])
const loadingDependentTasks = ref(false)
const commonRecipients = ref([
  'admin@example.com',
  'ops@example.com',
  'dev@example.com'
])

const formData = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 计算总内存
const totalMemory = computed(() => {
  const memMap = { '2g': 2, '4g': 4, '8g': 8, '16g': 16 }
  return memMap[formData.value.executorMemory] || 2
})

// 表单验证规则
const rules = ref({
  scheduleCron: [
    {
      validator: (rule, value, callback) => {
        if (formData.value.scheduleType === 'scheduled' && !value) {
          callback(new Error('请配置Cron表达式'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  retryTimes: [
    { required: true, message: '请设置重试次数', trigger: 'change' }
  ],
  retryInterval: [
    { required: true, message: '请设置重试间隔', trigger: 'change' }
  ],
  timeout: [
    { required: true, message: '请设置超时时间', trigger: 'change' }
  ]
})

// 事件处理
function handleScheduleTypeChange() {
  if (formData.value.scheduleType === 'manual') {
    formData.value.scheduleCron = ''
  } else {
    // 默认每天凌晨2点执行
    formData.value.scheduleCron = '0 0 2 * * ?'
  }
}

function searchDependentTasks(query) {
  if (!query) {
    dependentTaskOptions.value = []
    return
  }

  loadingDependentTasks.value = true
  // TODO: 调用API搜索任务
  setTimeout(() => {
    dependentTaskOptions.value = [
      { id: 1, name: 'sync_user_data', type: '数据集成' },
      { id: 2, name: 'daily_order_summary', type: 'SQL任务' },
      { id: 3, name: 'product_stats', type: 'SQL任务' }
    ].filter(task => task.name.includes(query))
    loadingDependentTasks.value = false
  }, 500)
}

// 表单验证
async function validate() {
  return await formRef.value?.validate()
}

function resetFields() {
  formRef.value?.resetFields()
}

defineExpose({
  validate,
  resetFields
})
</script>

<style scoped lang="scss">
.advanced-step {
  padding: 16px;
}

.config-section {
  margin-bottom: 24px;

  &:last-child {
    margin-bottom: 0;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
  }
}

.radio-content {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .radio-title {
    font-weight: 500;
  }

  .radio-desc {
    font-size: 12px;
    color: #909399;
  }
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .option-desc {
    font-size: 12px;
    color: #909399;
  }
}

.checkbox-content {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .checkbox-desc {
    font-size: 12px;
    color: #909399;
  }
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;

  .task-name {
    flex: 1;
  }
}

:deep(.el-radio),
:deep(.el-checkbox) {
  display: flex;
  white-space: normal;
  height: auto;
  margin-bottom: 12px;

  .el-radio__label,
  .el-checkbox__label {
    white-space: normal;
  }
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>
