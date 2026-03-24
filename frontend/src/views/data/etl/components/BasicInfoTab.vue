<template>
  <el-descriptions :column="2" border>
    <el-descriptions-item label="任务编码">
      <span v-if="!isEdit">{{ form.taskCode }}</span>
      <el-input v-else v-model="form.taskCode" placeholder="请输入任务编码" />
    </el-descriptions-item>
    <el-descriptions-item label="任务分类">
      <span v-if="!isEdit">{{ form.category || '-' }}</span>
      <el-input v-else v-model="form.category" placeholder="请输入任务分类" />
    </el-descriptions-item>
    <el-descriptions-item label="ETL类型" :span="2">
      <span v-if="!isEdit">{{ getEtlTypeText(form.etlType) }}</span>
      <el-select v-else v-model="form.etlType" style="width: 200px">
        <el-option label="STG采集" value="extract" />
        <el-option label="DWD转换" value="transform" />
        <el-option label="ODS加载" value="load" />
        <el-option label="全量ETL" value="full" />
      </el-select>
    </el-descriptions-item>
    <el-descriptions-item label="执行器类型" :span="2">
      <span v-if="!isEdit">{{ getExecutorTypeText(form.executorType) }}</span>
      <el-select v-else v-model="form.executorType" style="width: 200px">
        <el-option label="模拟执行器" value="mock" />
        <el-option label="DataX" value="datax" />
        <el-option label="Spark SQL" value="spark" />
        <el-option label="Python脚本" value="python" />
      </el-select>
    </el-descriptions-item>
    <el-descriptions-item label="执行策略">
      <span v-if="!isEdit">{{ form.executeStrategy === 'full' ? '全量' : '增量' }}</span>
      <el-radio-group v-else v-model="form.executeStrategy">
        <el-radio value="full">全量</el-radio>
        <el-radio value="increment">增量</el-radio>
      </el-radio-group>
    </el-descriptions-item>
    <el-descriptions-item label="任务状态">
      <span v-if="!isEdit">{{ form.status === '0' ? '启用' : '停用' }}</span>
      <el-switch v-else v-model="form.status" active-value="0" inactive-value="1" />
    </el-descriptions-item>
    <el-descriptions-item label="任务描述" :span="2">
      <span v-if="!isEdit">{{ form.description || '-' }}</span>
      <el-input v-else v-model="form.description" type="textarea" :rows="3" />
    </el-descriptions-item>
    <el-descriptions-item label="创建时间">{{ form.createTime }}</el-descriptions-item>
    <el-descriptions-item label="更新时间">{{ form.updateTime }}</el-descriptions-item>
  </el-descriptions>
</template>

<script setup>
defineProps({
  form: { type: Object, required: true },
  isEdit: { type: Boolean, default: false }
})

function getEtlTypeText(etlType) {
  const texts = { extract: 'STG采集', transform: 'DWD转换', load: 'ODS加载', full: '全量ETL' }
  return texts[etlType] || etlType
}

function getExecutorTypeText(executorType) {
  const texts = { mock: '模拟', datax: 'DataX', spark: 'Spark', python: 'Python' }
  return texts[executorType] || executorType
}
</script>
