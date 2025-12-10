<template>
  <div class="app-container">
    <el-page-header :content="pageTitle" @back="goBack" />
    <div style="margin-top: 16px">
        <component :is="currentComp" ref="detailRef" />
    </div>

    <el-card style="margin-top: 16px">
        <template #header>
        <span>任务调度策略</span>
        </template>
        <el-form :model="taskDetailForm" label-width="120px">
        <el-form-item label="调度策略">
        <el-radio-group v-model="taskDetailForm.schedule.type">
            <el-radio label="manual">手动</el-radio>
            <el-radio label="cron">定时</el-radio>
        </el-radio-group>
        <div v-if="taskDetailForm.schedule.type==='cron'" style="display: inline-flex; align-items: center; margin-left: 12px">
            <el-input v-model="taskDetailForm.schedule.cronExpr" placeholder="cron表达式" style="width: 240px" />
            <el-button style="margin-left: 8px" @click="handleShowCron">生成</el-button>
        </div>
        </el-form-item>
        <el-form-item label="分组调度">
            <el-select v-model="taskDetailForm.schedule.group" allow-create filterable default-first-option placeholder="请选择分组" style="width: 240px">
                <el-option v-for="g in scheduleGroups" :key="g" :label="g" :value="g" />
            </el-select>
        </el-form-item>
        </el-form>
    </el-card>

    <!-- CronTab 选择器弹窗 -->
    <el-dialog title="Cron表达式生成器" v-model="openCron" append-to-body destroy-on-close>
      <crontab @hide="openCron=false" @fill="crontabFill" :expression="expression" />
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="openCron=false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>
    <div style="margin-top: 16px; text-align: right">
      <el-button @click="goBack">返 回</el-button>
      <el-button type="primary" @click="handleSave">保 存</el-button>
      <el-button type="info" @click="handleValidate">校 验</el-button>
    </div>
  </div>
</template>

<script setup>
import Crontab from '@/components/Crontab'
import SingleTableSyncDetail from './offline/components/singleTableSyncDetail.vue'
import MultiTableSyncDetail from './offline/components/multiTableSyncDetail.vue'
import { useRoute, useRouter } from 'vue-router'
import { addTask, updateTask, getTask } from '@/api/dataintegration'
const route = useRoute()
const router = useRouter()
const { proxy } = getCurrentInstance()


function goBack() {
  router.back()
}

async function handleSave() {
  try {
    taskDetailForm.detail = detailRef.value?.getForm?.()
    if (!taskDetailForm.detail) {
      proxy.$modal.msgError('表单未就绪')
      return
    }
    const payload = {
      taskName: pageTitle.value,
      taskType: type.value,
      schedule: taskDetailForm.schedule,
      detail: taskDetailForm.detail
    }
    const id = route.params.id
      if (id && id !== 'new') {
        console.log('updateTask', id, payload)
      await updateTask(id, payload)
      proxy.$modal.msgSuccess('保存成功')
    } else {
      await addTask(payload)
      proxy.$modal.msgSuccess('保存成功')
    }
    router.push({ name: 'DataIntegrationTasks' })
  } catch (e) {
    proxy.$modal.msgError('保存失败')
  }
}


const handleValidate = () => {
    try {
        if (!taskDetailForm.detail) {
            proxy.$modal.msgError('表单未保存')
            return
        }

        if (!taskDetailForm.detail.mode) {
            proxy.$modal.msgError('请选择任务执行模式')
            return
        }
        // 检查是否指定的增量字段
        if (taskDetailForm.detail.mode.type && taskDetailForm.detail.mode.type === 'incremental') {
            if (!taskDetailForm.detail.mode.incrementField) {
                proxy.$modal.msgError('增量字段未指定')
                return
            }
        }
        proxy.$modal.msgSuccess('校验通过')
    } catch (e) {
        proxy.$modal.msgError('校验失败')
    }
}


// 任务调度信息
const taskDetailForm = reactive({
  schedule: {
    type: 'manual',
    cronExpr: '',
    group: '',
  },
  detail: {}
})

const scheduleGroups = ref([])
const openCron = ref(false)
const expression = ref('')

function handleShowCron() {
  expression.value = taskDetailForm.schedule.cronExpr
  openCron.value = true
}

function crontabFill(value) {
  taskDetailForm.schedule.cronExpr = value
}



const type = computed(() => (route.query.type || 'single'))
const pageTitle = computed(() => type.value === 'multi' ? '分库分表离线同步' : '单表离线同步')
const currentComp = computed(() => type.value === 'multi' ? MultiTableSyncDetail : SingleTableSyncDetail)
const detailRef = ref()


onMounted(() => {
  const id = route.params.id
  if (id && id !== 'new') {
    getTask(id).then(res => {
        const data = res.data || {}
        taskDetailForm.schedule = data.schedule || { type: 'manual', cronExpr: '', group: '' }
        taskDetailForm.detail = data.detail || {}
        detailRef.value?.setForm?.(taskDetailForm.detail)
    })
  }
})

</script>

<style scoped>
</style>

