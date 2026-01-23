<template>
  <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
    <el-form-item label="STG表" prop="sourceTable" required>
      <hive-table-select
        v-model="formData.sourceTable"
        schema="stg"
        @change="handleSourceTableChange"
        placeholder="请选择STG层的表"
        style="width: 100%"
      />
    </el-form-item>

    <el-form-item label="清洗规则">
      <el-input
        v-model="formData.transformRules"
        type="textarea"
        :rows="3"
        placeholder="可选，如：去除空值、数据格式转换等规则"
      />
      <div class="form-tip">对STG数据进行清洗、去重、格式转换等处理</div>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive } from 'vue'
import HiveTableSelect from '../HiveTableSelect'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'source-table-change'])

const formRef = ref()
const formData = reactive(props.modelValue)

const rules = {
  sourceTable: [{ required: true, message: '请选择STG表', trigger: 'change' }]
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
