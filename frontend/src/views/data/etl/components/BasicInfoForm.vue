<template>
  <el-row :gutter="20">
    <el-col :span="12">
      <el-form-item label="任务名称">
        <el-input v-model="formData.taskName" placeholder="请输入任务名称" />
      </el-form-item>
    </el-col>
    <el-col :span="12">
      <el-form-item label="任务编码">
        <el-input v-model="formData.taskCode" placeholder="请输入任务编码" />
      </el-form-item>
    </el-col>
    <el-col :span="12">
      <el-form-item label="ETL类型">
        <el-select v-model="formData.etlType" placeholder="请选择ETL类型" style="width: 100%" @change="handleEtlTypeChange">
          <el-option label="数据集成" value="data_integration" />
          <el-option label="SQL任务" value="sql_task" />
        </el-select>
      </el-form-item>
    </el-col>
    <el-col :span="12">
      <el-form-item label="执行器类型">
        <el-input :value="getExecutorLabel(formData.executorType)" readonly placeholder="根据任务类型自动选择" style="width: 100%">
          <template #append>
            <el-tag :type="getExecutorTagType(formData.executorType)">
              {{ getExecutorLabel(formData.executorType) }}
            </el-tag>
          </template>
        </el-input>
      </el-form-item>
    </el-col>
    <el-col :span="12" v-if="formData.etlType === 'data_integration'">
      <el-form-item label="执行策略">
        <el-select v-model="formData.executeStrategy" placeholder="请选择执行策略" style="width: 100%">
          <el-option label="全量" value="full" />
          <el-option label="增量" value="increment" />
        </el-select>
      </el-form-item>
    </el-col>
    <el-col :span="12">
      <el-form-item label="状态">
        <el-radio-group v-model="formData.status">
          <el-radio v-for="dict in statusOptions" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-col>
    <el-col :span="24">
      <el-form-item label="任务描述">
        <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="请输入任务描述" />
      </el-form-item>
    </el-col>
  </el-row>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  statusOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const formData = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// ETL类型映射到执行器类型
const ETL_TYPE_EXECUTOR_MAP = {
  data_integration: 'datax',
  sql_task: 'spark'
}

// 执行器类型标签
const EXECUTOR_LABELS = {
  datax: 'DataX',
  spark: 'Spark SQL',
  mock: '模拟执行器',
  python: 'Python脚本'
}

// 执行器类型标签颜色
const EXECUTOR_TAG_TYPES = {
  datax: 'success',
  spark: 'primary',
  mock: 'info',
  python: 'warning'
}

// 处理ETL类型变化
const handleEtlTypeChange = (etlType) => {
  if (etlType) {
    const executorType = ETL_TYPE_EXECUTOR_MAP[etlType]
    if (executorType) {
      formData.value = {
        ...formData.value,
        executorType: executorType,
        // 如果是SQL任务，清空执行策略
        executeStrategy: etlType === 'sql_task' ? undefined : formData.value.executeStrategy
      }
    }
  }
}

// 获取执行器标签
const getExecutorLabel = (executorType) => {
  return EXECUTOR_LABELS[executorType] || '-'
}

// 获取执行器标签类型
const getExecutorTagType = (executorType) => {
  return EXECUTOR_TAG_TYPES[executorType] || 'info'
}
</script>
