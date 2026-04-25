<template>
  <el-form ref="innerFormRef" :model="form" :rules="rules" label-width="100px" class="detail-form">
    <el-card shadow="never" class="detail-section">
      <template #header><span>基础信息</span></template>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="任务名称" prop="taskName">
            <el-input v-model="form.taskName" placeholder="例如：订单贴源同步" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="任务编码" prop="taskCode">
            <el-input v-model="form.taskCode" :disabled="!!form.taskId" placeholder="例如：sync_order_info" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="负责人" prop="owner">
            <el-input v-model="form.owner" placeholder="可选" />
          </el-form-item>
        </el-col>
        <el-col v-if="form.taskId" :span="12">
          <el-form-item label="任务状态" prop="status">
            <el-select v-model="form.status" placeholder="请选择状态">
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="备注">
            <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="说明这个任务为什么存在、负责同步什么。" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="detail-section">
      <template #header><span>源表到目标表映射</span></template>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="源数据源" prop="sourceDataSourceId">
            <el-select v-model="form.sourceDataSourceId" filterable placeholder="请选择源数据源" @change="$emit('source-ds-change', $event)">
              <el-option v-for="item in dataSourceOptions" :key="item.dataSourceId" :label="item.dataSourceName" :value="item.dataSourceId" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="源库名" prop="sourceDatabaseName">
            <el-input v-model="form.sourceDatabaseName" placeholder="可选，例如：biz" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="目标数据源" prop="targetDataSourceId">
            <el-select v-model="form.targetDataSourceId" filterable placeholder="请选择目标数据源">
              <el-option v-for="item in dataSourceOptions" :key="item.dataSourceId" :label="item.dataSourceName" :value="item.dataSourceId" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="源表名" prop="sourceTableName">
            <el-input v-model="form.sourceTableName" placeholder="例如：order_info" @input="$emit('source-table-input')" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="目标 Schema" prop="targetSchemaName">
            <el-input v-model="form.targetSchemaName" placeholder="例如：ods" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="目标表名" prop="targetTableName">
            <el-input v-model="form.targetTableName" placeholder="例如：ods_order_info" @input="$emit('target-table-input')" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="detail-section">
      <template #header><span>执行与调度</span></template>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="加载方式" prop="loadType">
            <el-radio-group v-model="form.loadType">
              <el-radio value="full">全量</el-radio>
              <el-radio value="incremental">增量</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="写入模式" prop="writeMode">
            <el-select v-model="form.writeMode" placeholder="请选择写入模式">
              <el-option label="覆盖" value="overwrite" />
              <el-option label="追加" value="append" />
              <el-option label="更新插入" value="upsert" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="执行器" prop="executorType">
            <el-select v-model="form.executorType" placeholder="请选择执行器">
              <el-option
                v-for="item in supportedExecutors"
                :key="item.value"
                :label="item.label"
                :value="item.value"
                :disabled="item.disabled"
              />
            </el-select>
            <div class="form-tip">{{ currentExecutorHint }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="调度方式" prop="scheduleType">
            <el-radio-group v-model="form.scheduleType">
              <el-radio value="manual">手动</el-radio>
              <el-radio value="cron">Cron</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col v-if="form.scheduleType === 'cron'" :span="24">
          <el-form-item label="Cron 表达式" prop="cronExpression">
            <el-input v-model="form.cronExpression" placeholder="例如：0 1 * * *" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="detail-section">
      <template #header><span>高级配置</span></template>
      <el-form-item label="任务配置">
        <el-input v-model="form.taskConfigText" type="textarea" :rows="8" placeholder='例如：{"batchSize":1000}' />
      </el-form-item>
    </el-card>
  </el-form>
</template>

<script setup>
defineProps({
  form: { type: Object, required: true },
  rules: { type: Object, required: true },
  dataSourceOptions: { type: Array, default: () => [] },
  statusOptions: { type: Array, default: () => [] },
  supportedExecutors: { type: Array, default: () => [] },
  currentExecutorHint: { type: String, default: '' },
})

defineEmits(['source-ds-change', 'source-table-input', 'target-table-input'])

const innerFormRef = ref()

function validate() {
  return innerFormRef.value?.validate()
}

function clearValidate() {
  innerFormRef.value?.clearValidate()
}

defineExpose({ validate, clearValidate })
</script>

<style scoped>
.detail-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-section {
  border-radius: 16px;
}

.detail-section :deep(.el-card__header) {
  padding: 16px 20px;
  font-weight: 600;
}

.form-tip {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
