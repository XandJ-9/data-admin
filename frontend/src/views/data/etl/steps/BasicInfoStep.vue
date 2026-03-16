<template>
  <div class="basic-info-step">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="140px"
      label-position="right"
    >
      <el-alert
        title="基本信息"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 24px"
      >
        配置任务的基本信息，包括任务名称、类型和所属业务域
      </el-alert>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="任务名称" prop="taskName">
            <el-input
              v-model="formData.taskName"
              placeholder="请输入任务名称"
              clearable
              maxlength="100"
              show-word-limit
            >
              <template #append>
                <el-button :icon="Refresh" @click="handleAutoGenerate" />
              </template>
            </el-input>
            <div class="form-tip">
              建议使用有意义的名称，如：sync_user_to_dw、daily_order_summary
            </div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="任务编码" prop="taskCode">
            <el-input
              v-model="formData.taskCode"
              placeholder="自动生成，可修改"
              clearable
              maxlength="50"
            />
            <div class="form-tip">唯一标识，建议使用英文和下划线</div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="ETL类型" prop="etlType">
            <el-select
              v-model="formData.etlType"
              placeholder="请选择ETL类型"
              style="width: 100%"
              @change="handleEtlTypeChange"
            >
              <el-option
                v-for="type in etlTypeOptions"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              >
                <div class="option-content">
                  <span class="option-label">{{ type.label }}</span>
                  <span class="option-desc">{{ type.description }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="所属业务域" prop="businessDomain">
            <el-select
              v-model="formData.businessDomain"
              placeholder="请选择业务域"
              style="width: 100%"
              filterable
              allow-create
            >
              <el-option
                v-for="domain in businessDomains"
                :key="domain.value"
                :label="domain.label"
                :value="domain.value"
              />
            </el-select>
            <div class="form-tip">可输入自定义业务域</div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="优先级" prop="priority">
            <el-radio-group v-model="formData.priority">
              <el-radio label="low">
                <div class="radio-content">
                  <el-tag size="small" type="info">低</el-tag>
                  <span>资源受限时优先让出</span>
                </div>
              </el-radio>
              <el-radio label="medium">
                <div class="radio-content">
                  <el-tag size="small" type="warning">中</el-tag>
                  <span>默认优先级</span>
                </div>
              </el-radio>
              <el-radio label="high">
                <div class="radio-content">
                  <el-tag size="small" type="danger">高</el-tag>
                  <span>优先执行</span>
                </div>
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态" prop="status">
            <el-radio-group v-model="formData.status">
              <el-radio label="0">
                <el-tag type="success">启用</el-tag>
                <span style="margin-left: 8px">创建后立即启用</span>
              </el-radio>
              <el-radio label="1">
                <el-tag type="info">停用</el-tag>
                <span style="margin-left: 8px">创建后暂不启用</span>
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="24">
          <el-form-item label="任务描述" prop="description">
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入任务描述，说明任务的用途和业务场景"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 执行器类型提示 -->
      <el-row :gutter="24">
        <el-col :span="24">
          <el-form-item label="执行器类型">
            <el-alert
              :title="`当前将使用 ${getExecutorLabel(formData.executorType)} 执行器`"
              type="success"
              :closable="false"
              show-icon
            >
              <template #default>
                <div>系统已根据任务类型自动选择最合适的执行器</div>
                <div v-if="formData.executorType === 'datax'">
                  DataX：适合异构数据源之间的数据同步，支持多种数据库和文件格式
                </div>
                <div v-else-if="formData.executorType === 'spark'">
                  Spark SQL：适合大规模数据计算和复杂SQL转换，支持分布式处理
                </div>
              </template>
            </el-alert>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  isEdit: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const formRef = ref()

const formData = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// ETL类型选项
const etlTypeOptions = ref([
  {
    value: 'data_integration',
    label: '数据集成',
    description: '数据源之间的同步和迁移',
    icon: 'Connection'
  },
  {
    value: 'sql_task',
    label: 'SQL任务',
    description: '使用Spark SQL进行数据转换',
    icon: 'DataAnalysis'
  }
])

// 业务域选项
const businessDomains = ref([
  { value: 'trading', label: '交易域' },
  { value: 'user', label: '用户域' },
  { value: 'logistics', label: '物流域' },
  { value: 'marketing', label: '营销域' },
  { value: 'finance', label: '财务域' },
  { value: 'common', label: '公共域' }
])

// 表单验证规则
const rules = ref({
  taskName: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  taskCode: [
    { required: true, message: '请输入任务编码', trigger: 'blur' },
    { pattern: /^[A-Z][A-Z0-9_]*$/, message: '任务编码必须以大写字母开头，只能包含大写字母、数字和下划线', trigger: 'blur' }
  ],
  etlType: [
    { required: true, message: '请选择ETL类型', trigger: 'change' }
  ],
  businessDomain: [
    { required: true, message: '请选择业务域', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ]
})

// ETL类型映射到执行器类型
const ETL_TYPE_EXECUTOR_MAP = {
  data_integration: 'datax',
  sql_task: 'spark'
}

// 执行器标签
const EXECUTOR_LABELS = {
  datax: 'DataX',
  spark: 'Spark SQL'
}

// 处理ETL类型变化
function handleEtlTypeChange(etlType) {
  const executorType = ETL_TYPE_EXECUTOR_MAP[etlType]
  if (executorType) {
    formData.value = {
      ...formData.value,
      executorType: executorType,
      // 清空不相关的配置
      extractMode: etlType === 'sql_task' ? undefined : formData.value.extractMode,
      sqlScript: etlType === 'data_integration' ? undefined : formData.value.sqlScript
    }
  }
}

// 自动生成任务名称
function handleAutoGenerate() {
  const domain = formData.value.businessDomain || 'common'
  const type = formData.value.etlType === 'data_integration' ? 'sync' : 'transform'
  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')

  formData.value.taskName = `${domain}_${type}_${timestamp}`

  // 自动生成任务编码
  formData.value.taskCode = `${domain.toUpperCase()}_${type.toUpperCase()}_${Date.now().toString(36).toUpperCase()}`
}

// 获取执行器标签
function getExecutorLabel(executorType) {
  return EXECUTOR_LABELS[executorType] || '-'
}

// 表单验证
async function validate() {
  return await formRef.value?.validate()
}

// 重置表单
function resetFields() {
  formRef.value?.resetFields()
}

// 暴露方法
defineExpose({
  validate,
  resetFields
})
</script>

<style scoped lang="scss">
.basic-info-step {
  padding: 16px;
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .option-label {
    font-weight: 500;
  }

  .option-desc {
    font-size: 12px;
    color: #909399;
  }
}

.radio-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

:deep(.el-radio) {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  white-space: normal;
  height: auto;

  .el-radio__label {
    display: flex;
    align-items: center;
  }
}
</style>
