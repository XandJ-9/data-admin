<template>
  <div class="simple-task-create">
    <!-- 场景选择阶段 -->
    <transition name="fade" mode="out-in">
      <div v-if="currentStage === 'scenario'" key="scenario" class="stage-container">
        <scenario-selector v-model="selectedScenario" @select="handleScenarioSelect" />
      </div>

      <!-- 配置向导阶段 -->
      <div v-else-if="currentStage === 'wizard'" key="wizard" class="stage-container">
        <simplified-wizard
          :scenario="selectedScenario"
          @submit="handleSubmit"
          @cancel="handleCancel"
        />
      </div>

      <!-- 执行监控阶段 -->
      <div v-else-if="currentStage === 'monitor'" key="monitor" class="stage-container">
        <execution-monitor
          :task-id="createdTaskId"
          :execution-id="executionId"
          @back="handleBackToList"
          @view-task="handleViewTask"
        />
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ScenarioSelector from './components/ScenarioSelector.vue'
import SimplifiedWizard from './components/SimplifiedWizard.vue'
import ExecutionMonitor from './components/ExecutionMonitor.vue'
import { addTask, executeTask } from '@/api/data/integration'

const router = useRouter()

const currentStage = ref('scenario') // scenario | wizard | monitor
const selectedScenario = ref('')
const createdTaskId = ref('')
const executionId = ref('')

function handleScenarioSelect(scenario) {
  selectedScenario.value = scenario
  setTimeout(() => {
    currentStage.value = 'wizard'
  }, 300)
}

async function handleSubmit(taskData) {
  try {
    // 创建任务
    const payload = buildTaskPayload(taskData)
    const res = await addTask(payload)
    createdTaskId.value = res.data.taskId

    // 如果是立即执行
    if (taskData.scheduleType === 'manual') {
      const execRes = await executeTask(createdTaskId.value)
      executionId.value = execRes.data.executionId
      currentStage.value = 'monitor'
    } else {
      // 定时任务，跳转到任务列表
      router.push({ name: 'DataIntegrationTasks' })
    }
  } catch (error) {
    console.error('创建任务失败:', error)
    throw error
  }
}

function handleCancel() {
  // 返回场景选择
  currentStage.value = 'scenario'
  selectedScenario.value = ''
}

function handleBackToList() {
  router.push({ name: 'DataIntegrationTasks' })
}

function handleViewTask() {
  router.push({
    name: 'DataIntegrationTaskDetail',
    params: { id: createdTaskId.value }
  })
}

function buildTaskPayload(wizardData) {
  // 将向导数据转换为后端API格式
  return {
    taskName: wizardData.taskName,
    taskType: wizardData.taskType,
    targetLayer: wizardData.targetLayer,
    executorType: wizardData.executorType,
    status: '0',
    remark: wizardData.remark || '',
    schedule: {
      type: wizardData.scheduleType,
      cronExpr: wizardData.scheduleType === 'scheduled' ? wizardData.scheduleCron : ''
    },
    detail: wizardData.detail,
    incrementalStrategy: wizardData.syncMode === 'full' ? 'full' : `incremental_${wizardData.incrementalField}`,
    incrementalField: wizardData.incrementalField || '',
    batchSize: wizardData.batchSize,
    concurrency: wizardData.concurrency
  }
}
</script>

<style scoped>
.simple-task-create {
  min-height: calc(100vh - 120px);
  background-color: #f5f7fa;
}

.stage-container {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
