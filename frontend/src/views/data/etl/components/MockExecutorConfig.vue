<template>
  <el-card shadow="never" class="config-card">
    <template #header>
      <span>Mock执行器配置</span>
    </template>

    <el-alert
      title="Mock执行器说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    >
      Mock执行器用于开发测试，模拟ETL任务执行，不连接真实数据源。执行结果为随机生成。
    </el-alert>

    <el-form :model="mockConfig" label-width="140px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="超时时间（秒）">
            <el-input-number
              v-model="mockConfig.timeout"
              :min="10"
              :max="3600"
              placeholder="超时时间"
              style="width: 100%"
            />
            <div class="form-item-tip">
              <el-text size="small" type="info">任务执行超时时间</el-text>
            </div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="重试次数">
            <el-input-number
              v-model="mockConfig.retryTimes"
              :min="0"
              :max="5"
              placeholder="重试次数"
              style="width: 100%"
            />
            <div class="form-item-tip">
              <el-text size="small" type="info">执行失败后的重试次数</el-text>
            </div>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      timeout: 300,
      retryTimes: 3
    })
  }
})

const emit = defineEmits(['update:modelValue'])

const mockConfig = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})
</script>

<style scoped>
.config-card {
  margin-bottom: 20px;
}

.form-item-tip {
  margin-top: 5px;
  line-height: 1.4;
}
</style>
