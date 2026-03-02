<template>
  <div class="task-form">
    <!-- 基本信息配置 -->
    <el-divider content-position="left">基本信息</el-divider>
    <BasicInfoForm
      v-model="formData"
      :status-options="statusOptions"
    />

    <!-- 数据源配置（仅数据集成任务显示） -->
    <template v-if="formData.taskType === 'data_integration'">
      <el-divider content-position="left">数据源配置</el-divider>
      <SourceTargetForm
        v-model="formData"
        :datasource-options="datasourceOptions"
        :source-table-options="sourceTableOptions"
        :target-table-options="targetTableOptions"
        @source-datasource-change="handleSourceDatasourceChange"
        @target-datasource-change="handleTargetDatasourceChange"
      />
    </template>

    <!-- SQL配置（仅SQL任务显示） -->
    <template v-if="formData.taskType === 'sql_task'">
      <el-divider content-position="left">SQL配置</el-divider>
      <SQLConfigForm v-model="formData" />
    </template>

    <!-- 执行器配置 -->
    <el-divider content-position="left">执行器配置</el-divider>

    <!-- Mock执行器 -->
    <MockExecutorConfig
      v-if="formData.executorType === 'mock'"
      v-model="executorParamsConfig"
    />

    <!-- DataX执行器 -->
    <DataXExecutorConfig
      v-if="formData.executorType === 'datax'"
      v-model="executorParamsConfig"
      :form="formData"
      :datasource-options="datasourceOptions"
    />

    <!-- Spark SQL执行器 -->
    <el-alert
      v-if="formData.executorType === 'spark'"
      title="Spark SQL执行器"
      type="info"
      :closable="false"
      show-icon
    >
      Spark SQL执行器配置正在开发中，敬请期待...
      <br/>
      当前SQL任务类型已支持，后续将提供完整的Spark SQL配置界面。
    </el-alert>

    <!-- Python脚本执行器（占位） -->
    <el-alert
      v-if="formData.executorType === 'python'"
      title="Python脚本执行器"
      type="info"
      :closable="false"
      show-icon
    >
      Python脚本执行器正在开发中，敬请期待...
    </el-alert>

    <!-- 其他配置 -->
    <el-divider content-position="left">其他配置</el-divider>
    <el-row :gutter="20">
      <el-col :span="24">
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="2" placeholder="请输入备注" />
        </el-form-item>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import BasicInfoForm from './BasicInfoForm.vue'
import SourceTargetForm from './SourceTargetForm.vue'
import SQLConfigForm from './SQLConfigForm.vue'
import MockExecutorConfig from './MockExecutorConfig.vue'
import DataXExecutorConfig from './DataXExecutorConfig.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  datasourceOptions: {
    type: Array,
    default: () => []
  },
  sourceTableOptions: {
    type: Array,
    default: () => []
  },
  targetTableOptions: {
    type: Array,
    default: () => []
  },
  statusOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'source-datasource-change', 'target-datasource-change'])

const formRef = ref(null)

const formData = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 执行器参数配置（使用命名空间结构）
const executorParamsConfig = computed({
  get: () => {
    const params = formData.value.executorParams || {}

    // 根据执行器类型返回对应的配置
    if (formData.value.executorType === 'datax') {
      return {
        reader: params.datax?.reader || {},
        writer: params.datax?.writer || {},
        speed: params.datax?.speed || {},
        ...params
      }
    } else if (formData.value.executorType === 'mock') {
      return {
        timeout: params.timeout || 300,
        retryTimes: params.retryTimes || 3
      }
    }

    return params
  },
  set: (val) => {
    let newParams = { ...formData.value.executorParams }

    // 根据执行器类型组织配置
    if (formData.value.executorType === 'datax') {
      newParams.datax = {
        reader: val.reader || {},
        writer: val.writer || {},
        speed: val.speed || {}
      }
      // 保留其他参数
      newParams.timeout = val.timeout
      newParams.retryTimes = val.retryTimes
    } else if (formData.value.executorType === 'mock') {
      newParams.timeout = val.timeout
      newParams.retryTimes = val.retryTimes
    } else {
      newParams = val
    }

    formData.value = {
      ...formData.value,
      executorParams: newParams
    }
  }
})

// 监听任务类型变化，初始化默认配置
watch(() => formData.value.taskType, (newTaskType, oldTaskType) => {
  if (newTaskType && newTaskType !== oldTaskType) {
    // 数据集成任务使用DataX执行器
    if (newTaskType === 'data_integration' && !formData.value.executorParams?.datax) {
      const defaultParams = {
        timeout: 300,
        retryTimes: 3,
        datax: {
          reader: {
            column: [],
            querySql: ''
          },
          writer: {
            writeMode: 'append',
            fileType: 'text',
            fieldDelimiter: ',',
            compress: 'gzip'
          },
          speed: {
            channel: 1,
            byte: 1048576,
            record: 100000
          }
        },
        incremental: {
          enabled: false,
          field: '',
          strategy: 'timestamp'
        },
        multi_tenant: {
          enabled: false,
          tenant_id_field: '',
          tenant_id: '',
          tenant_source_ids: []
        }
      }
      formData.value.executorParams = defaultParams
    }
    // SQL任务使用Spark SQL执行器
    else if (newTaskType === 'sql_task' && !formData.value.executorParams?.spark) {
      const defaultParams = {
        timeout: 300,
        retryTimes: 3,
        spark: {
          sql: '',
          appName: '',
          executorMemory: '2g',
          executorCores: 2,
          executorInstances: 2
        }
      }
      formData.value.executorParams = defaultParams
    }
  }
})

// 监听执行器类型变化（保留兼容性）
watch(() => formData.value.executorType, (newType, oldType) => {
  if (newType && newType !== oldType) {
    // 初始化默认配置
    if (newType === 'datax' && !formData.value.executorParams?.datax) {
      const defaultParams = {
        timeout: 300,
        retryTimes: 3,
        datax: {
          reader: {
            column: [],
            querySql: ''
          },
          writer: {
            writeMode: 'append',
            fileType: 'text',
            fieldDelimiter: ',',
            compress: 'gzip'
          },
          speed: {
            channel: 1,
            byte: 1048576,
            record: 100000
          }
        },
        incremental: {
          enabled: false,
          field: '',
          strategy: 'timestamp'
        },
        multi_tenant: {
          enabled: false,
          tenant_id_field: '',
          tenant_id: '',
          tenant_source_ids: []
        }
      }
      formData.value.executorParams = defaultParams
    } else if (newType === 'spark' && !formData.value.executorParams?.spark) {
      const defaultParams = {
        timeout: 300,
        retryTimes: 3,
        spark: {
          sql: '',
          appName: '',
          executorMemory: '2g',
          executorCores: 2,
          executorInstances: 2
        }
      }
      formData.value.executorParams = defaultParams
    } else if (newType === 'mock' && !formData.value.executorParams?.timeout) {
      formData.value.executorParams = {
        timeout: 300,
        retryTimes: 3
      }
    }
  }
})

const handleSourceDatasourceChange = (value) => {
  emit('source-datasource-change', value)
}

const handleTargetDatasourceChange = (value) => {
  emit('target-datasource-change', value)
}

// 注意：验证规则移到父组件index.vue中定义，因为TaskForm组件本身不处理验证
// 父组件可以通过ref调用TaskForm的validate方法


// 暴露验证方法
const validate = () => {
  return formRef.value?.validate()
}

const resetFields = () => {
  formRef.value?.resetFields()
}

defineExpose({
  formRef,
  validate,
  resetFields
})
</script>

<style scoped>
.el-divider {
  margin: 20px 0;
}
</style>
