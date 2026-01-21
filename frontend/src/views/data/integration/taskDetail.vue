<template>
  <div class="app-container">
    <el-card>
      <div class="header-actions">
        <el-form :inline="true" :model="taskForm" class="demo-form-inline">
          <el-form-item label="任务名称">
            <el-input v-model="taskForm.name" placeholder="请输入任务名称" style="width: 320px" />
          </el-form-item>
          <el-form-item>
            <el-button @click="goBack">返回列表</el-button>
            <el-button type="primary" @click="handleSave">保 存</el-button>
            <!-- <el-button type="info" @click="handleValidate">校 验</el-button> -->
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>
        <span>任务配置</span>
      </template>
      <SyncConfigDetail v-model:detail="taskForm.detail" />
    </el-card>

    <!-- 调度配置 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <span>调度策略</span>
      </template>
      <el-form :model="taskForm" label-width="120px">
        <el-form-item label="调度策略">
          <el-radio-group v-model="taskForm.schedule.type">
            <el-radio label="manual">手动</el-radio>
            <el-radio label="cron">定时</el-radio>
          </el-radio-group>
          <div v-if="taskForm.schedule.type === 'cron'"
            style="display: inline-flex; align-items: center; margin-left: 12px">
            <el-input v-model="taskForm.schedule.cronExpr" placeholder="cron表达式" style="width: 240px" />
            <el-button style="margin-left: 8px" @click="handleShowCron">生成</el-button>
          </div>
        </el-form-item>
        <el-form-item label="分组调度">
          <el-select v-model="taskForm.schedule.group" allow-create filterable default-first-option placeholder="请选择分组"
            style="width: 240px">
            <el-option v-for="g in scheduleGroups" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- CronTab 选择器弹窗 -->
    <el-dialog title="Cron表达式生成器" v-model="openCron" append-to-body destroy-on-close>
      <crontab @hide="openCron = false" @fill="crontabFill" :expression="expression" />
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="openCron = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted, getCurrentInstance } from 'vue'
import Crontab from '@/components/Crontab'
import SyncConfigDetail from './components/SyncConfigDetail'
import { useRoute, useRouter } from 'vue-router'
import { addTask, updateTask, getTask, listTasks } from '@/api/data/integration'
import useTagsViewStore from '@/store/modules/tagsView'

const route = useRoute()
const router = useRouter()
const tagsViewStore = useTagsViewStore()
const { proxy } = getCurrentInstance()

const scheduleGroups = ref([])
const openCron = ref(false)
const expression = ref('')

const taskForm = reactive({
  name: '',
  type: undefined,
  detail: {},
  schedule: {
    type: 'manual',
    cronExpr: '',
    group: '',
  }
})

function addScheduleGroupOption(group) {
  const v = (group ?? '').toString().trim()
  if (!v) return
  if (!scheduleGroups.value.includes(v)) scheduleGroups.value.push(v)
}

async function loadScheduleGroups() {
  try {
    const res = await listTasks({ pageNum: 1, pageSize: 1000 })
    const rows = res?.rows || []
    const set = new Set()
    rows.forEach((t) => {
      const g = t?.schedule?.group
      const v = (g ?? '').toString().trim()
      if (v) set.add(v)
    })
    scheduleGroups.value = Array.from(set)
    addScheduleGroupOption(taskForm.schedule.group)
  } catch (_) {
    addScheduleGroupOption(taskForm.schedule.group)
  }
}

function goBack() {
  const visitedViews = tagsViewStore.visitedViews
  const view = visitedViews.find(v => v.path === route.path)
  if (view) {
    tagsViewStore.delView(view).then(() => {
        router.push({ name: 'DataIntegrationTasks' })
    })
  } else {
      router.push({ name: 'DataIntegrationTasks' })
  }
}

async function handleSave() {
  if (!taskForm.name) {
    proxy.$modal.msgError('请输入任务名称')
    return
  }
  if (!taskForm.type) {
    proxy.$modal.msgError('缺少任务类型')
    return
  }
  if (taskForm.schedule?.type === 'cron' && !taskForm.schedule?.cronExpr) {
    proxy.$modal.msgError('请输入cron表达式')
    return
  }
  
  try {
    const schedule = { ...(taskForm.schedule || {}) }
    if (schedule.type !== 'cron') schedule.cronExpr = ''
    const payload = {
      taskName: taskForm.name,
      taskType: taskForm.type,
      schedule,
      detail: taskForm.detail
    }
    const id = route.params.id
    if (id && id !== 'new') {
      await updateTask(id, payload)
      proxy.$modal.msgSuccess('保存成功')
    } else {
      await addTask(payload)
      proxy.$modal.msgSuccess('新增成功')
      // router.push({ name: 'DataIntegrationTasks' })
      goBack()
    }
  } catch (e) {
    proxy.$modal.msgError(e?.msg || e?.message || '保存失败')
  }
}

function handleShowCron() {
  expression.value = taskForm.schedule.cronExpr
  openCron.value = true
}

function crontabFill(value) {
  taskForm.schedule.cronExpr = value
}

watch(
  () => taskForm.schedule?.type,
  (type) => {
    if (type !== 'cron') taskForm.schedule.cronExpr = ''
  }
)

watch(
  () => taskForm.schedule?.group,
  (group) => {
    addScheduleGroupOption(group)
  }
)

onMounted(async () => {
  const id = route.params.id
  taskForm.type = route.query.type
  await loadScheduleGroups()
  if (id && id !== 'new') {
    getTask(id).then(res => {
      const data = res.data || {}
      taskForm.type = data.taskType || taskForm.type
      taskForm.name = data.taskName || ''
      taskForm.schedule = data.schedule || { type: 'manual', cronExpr: '', group: '' }
      taskForm.detail = data.detail || {}
      addScheduleGroupOption(taskForm.schedule.group)
    }).catch(() => {
        proxy.$modal.msgError('获取任务详情失败')
        goBack()
    })
  }
})

</script>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
}
</style>
