<template>
  <el-row :gutter="20">
    <el-col :span="12">
      <el-form-item label="源数据源">
        <el-select
          v-model="formData.sourceDatasourceId"
          filterable
          placeholder="请选择源数据源"
          style="width: 100%"
          @change="handleSourceDatasourceChange"
        >
          <el-option v-for="ds in datasourceOptions" :key="ds.dataSourceId" :label="ds.dataSourceName" :value="ds.dataSourceId" />
        </el-select>
      </el-form-item>
    </el-col>
    <el-col :span="12">
      <el-form-item label="目标数据源">
        <el-select
          v-model="formData.targetDatasourceId"
          filterable
          placeholder="请选择目标数据源"
          style="width: 100%"
          @change="handleTargetDatasourceChange"
        >
          <el-option v-for="ds in datasourceOptions" :key="ds.dataSourceId" :label="ds.dataSourceName" :value="ds.dataSourceId" />
        </el-select>
      </el-form-item>
    </el-col>
    <el-col :span="12">
      <el-form-item label="源表">
        <el-select
          v-model="formData.sourceTableId"
          filterable
          placeholder="请选择源表"
          style="width: 100%"
          :disabled="!formData.sourceDatasourceId"
        >
          <el-option v-for="table in sourceTableOptions" :key="table.id" :label="table.tableName" :value="table.id" />
        </el-select>
      </el-form-item>
    </el-col>
    <el-col :span="12">
      <el-form-item label="目标表">
        <el-select
          v-model="formData.targetTable"
          filterable
          placeholder="请选择或输入目标表"
          style="width: 100%"
          :disabled="!formData.targetDatasourceId"
          allow-create
          default-first-option
        >
          <el-option v-for="table in targetTableOptions" :key="table.id" :label="table.tableName" :value="table.tableName" />
        </el-select>
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
  }
})

const emit = defineEmits(['update:modelValue', 'source-datasource-change', 'target-datasource-change'])

const formData = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const handleSourceDatasourceChange = (value) => {
  emit('source-datasource-change', value)
}

const handleTargetDatasourceChange = (value) => {
  emit('target-datasource-change', value)
}
</script>
