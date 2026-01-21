<template>
  <div class="schedule-select">
    <el-radio-group v-model="scheduleType" @change="handleTypeChange">
      <el-radio label="simple">简单配置</el-radio>
      <el-radio label="cron">Cron表达式</el-radio>
    </el-radio-group>

    <!-- 简单配置 -->
    <div v-if="scheduleType === 'simple'" class="simple-config">
      <el-select v-model="simpleInterval" @change="handleSimpleChange" style="width: 200px; margin-right: 8px">
        <el-option label="每小时" value="hourly" />
        <el-option label="每天" value="daily" />
        <el-option label="每周" value="weekly" />
        <el-option label="每月" value="monthly" />
      </el-select>

      <el-time-picker
        v-if="simpleInterval !== 'hourly'"
        v-model="simpleTime"
        format="HH:mm"
        value-format="HH:mm"
        placeholder="选择时间"
        @change="handleSimpleChange"
      />

      <el-select
        v-if="simpleInterval === 'weekly'"
        v-model="simpleDayOfWeek"
        @change="handleSimpleChange"
        style="width: 120px; margin-left: 8px"
      >
        <el-option label="周一" value="1" />
        <el-option label="周二" value="2" />
        <el-option label="周三" value="3" />
        <el-option label="周四" value="4" />
        <el-option label="周五" value="5" />
        <el-option label="周六" value="6" />
        <el-option label="周日" value="0" />
      </el-select>

      <el-input-number
        v-if="simpleInterval === 'monthly'"
        v-model="simpleDayOfMonth"
        :min="1"
        :max="28"
        @change="handleSimpleChange"
        style="width: 100px; margin-left: 8px"
      />
      <span v-if="simpleInterval === 'monthly'" style="margin-left: 4px">号</span>
    </div>

    <!-- Cron表达式 -->
    <div v-else class="cron-config">
      <el-input v-model="cronExpression" placeholder="0 0 * * *" @change="handleCronChange" />
      <el-button style="margin-left: 8px" @click="showCronHelp">帮助</el-button>
    </div>

    <!-- 预览 -->
    <div v-if="nextRunTime" class="next-run-preview">
      <el-icon><Clock /></el-icon>
      下次执行时间: {{ nextRunTime }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { Clock } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '0 0 * * *'
  }
})

const emit = defineEmits(['update:modelValue'])

const scheduleType = ref('simple')
const simpleInterval = ref('daily')
const simpleTime = ref('00:00')
const simpleDayOfWeek = ref('1')
const simpleDayOfMonth = ref(1)
const cronExpression = ref('')

watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue && newValue !== cronExpression.value) {
      cronExpression.value = newValue
      scheduleType.value = 'cron'
    }
  },
  { immediate: true }
)

function handleTypeChange() {
  if (scheduleType.value === 'simple') {
    handleSimpleChange()
  } else {
    handleCronChange()
  }
}

function handleSimpleChange() {
  let cron = ''

  switch (simpleInterval.value) {
    case 'hourly':
      cron = '0 * * * *'
      break
    case 'daily':
      const [hour, minute] = simpleTime.value.split(':')
      cron = `${minute} ${hour} * * *`
      break
    case 'weekly':
      const [weekHour, weekMinute] = simpleTime.value.split(':')
      cron = `${weekMinute} ${weekHour} * * ${simpleDayOfWeek.value}`
      break
    case 'monthly':
      const [monthHour, monthMinute] = simpleTime.value.split(':')
      cron = `${monthMinute} ${monthHour} ${simpleDayOfMonth.value} * *`
      break
  }

  cronExpression.value = cron
  emit('update:modelValue', cron)
}

function handleCronChange() {
  emit('update:modelValue', cronExpression.value)
}

function showCronHelp() {
  // 打开cron帮助对话框
  // 可以使用现成的cron表达式生成器组件
}

const nextRunTime = computed(() => {
  if (!cronExpression.value) return ''

  // TODO: 解析cron表达式并计算下次执行时间
  // 这里可以使用cron-parser等库
  return '2024-01-22 00:00:00'
})
</script>

<style scoped>
.schedule-select {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.simple-config,
.cron-config {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.next-run-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border-radius: 4px;
  color: #409EFF;
  font-size: 13px;
}
</style>
