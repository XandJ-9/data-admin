<template>
  <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
    <el-form-item label="源业务库" prop="sourceDatasourceId" required>
      <datasource-select
        v-model="formData.sourceDatasourceId"
        @change="handleSourceChange"
        placeholder="请选择业务数据库"
        style="width: 100%"
      />
    </el-form-item>

    <el-form-item label="源表" prop="sourceTable" required>
      <table-select
        v-model="formData.sourceTable"
        :datasource-id="formData.sourceDatasourceId"
        @change="handleSourceTableChange"
        placeholder="请选择要同步的表"
        style="width: 100%"
      />
    </el-form-item>

    <el-form-item label="过滤条件">
      <el-input
        v-model="formData.whereCondition"
        type="textarea"
        :rows="2"
        placeholder="可选，如：status = 1 AND create_time >= '2024-01-01'"
      />
      <div class="form-tip">只同步满足条件的数据，留空则同步全部数据</div>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive } from 'vue'
import DatasourceSelect from '../DatasourceSelect'
import TableSelect from '../TableSelect'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'source-change', 'source-table-change'])

const formRef = ref()
const formData = reactive(props.modelValue)

const rules = {
  sourceDatasourceId: [{ required: true, message: '请选择源数据源', trigger: 'change' }],
  sourceTable: [{ required: true, message: '请选择源表', trigger: 'change' }]
}

function handleSourceChange() {
  emit('source-change')
}

function handleSourceTableChange() {
  emit('source-table-change')
}

async function validate() {
  return await formRef.value?.validate().catch(() => false)
}

defineExpose({
  validate
})
</script>

<style scoped>
.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
