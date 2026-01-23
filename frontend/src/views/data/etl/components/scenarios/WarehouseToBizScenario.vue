<template>
  <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
    <el-form-item label="数仓表" prop="sourceTable" required>
      <hive-table-select
        v-model="formData.sourceTable"
        @change="handleSourceTableChange"
        placeholder="请选择要导出的数仓表"
        style="width: 100%"
      />
    </el-form-item>

    <el-form-item label="目标业务库" prop="targetDatasourceId" required>
      <datasource-select
        v-model="formData.targetDatasourceId"
        @change="handleTargetChange"
        placeholder="请选择目标业务数据库"
        style="width: 100%"
      />
    </el-form-item>

    <el-form-item label="目标表" prop="targetTable" required>
      <table-select
        v-model="formData.targetTable"
        :datasource-id="formData.targetDatasourceId"
        placeholder="请选择或输入目标表名"
        allow-create
        style="width: 100%"
      />
    </el-form-item>

    <el-form-item label="写入模式">
      <el-radio-group v-model="formData.writeMode">
        <el-radio label="overwrite">覆盖模式</el-radio>
        <el-radio label="append">追加模式</el-radio>
      </el-radio-group>
      <div class="form-tip">覆盖：清空后写入；追加：保留原数据，新增数据</div>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive } from 'vue'
import DatasourceSelect from '../DatasourceSelect'
import TableSelect from '../TableSelect'
import HiveTableSelect from '../HiveTableSelect'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'source-table-change', 'target-change'])

const formRef = ref()
const formData = reactive(props.modelValue)

const rules = {
  sourceTable: [{ required: true, message: '请选择数仓表', trigger: 'change' }],
  targetDatasourceId: [{ required: true, message: '请选择目标数据源', trigger: 'change' }],
  targetTable: [{ required: true, message: '请选择目标表', trigger: 'change' }]
}

function handleSourceTableChange() {
  emit('source-table-change')
}

function handleTargetChange() {
  emit('target-change')
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
