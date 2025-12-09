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
    </div>
  </div>
</template>

<script setup>
import Crontab from '@/components/Crontab'
import SingleTableSyncDetail from './offline/components/singleTableSyncDetail.vue'
import MultiTableSyncDetail from './offline/components/multiTableSyncDetail.vue'
import { useRoute, useRouter } from 'vue-router'
const route = useRoute()
const router = useRouter()
const { proxy } = getCurrentInstance()

const type = computed(() => (route.query.type || 'single'))
const pageTitle = computed(() => type.value === 'multi' ? '分库分表离线同步' : '单表离线同步')
const currentComp = computed(() => type.value === 'multi' ? MultiTableSyncDetail : SingleTableSyncDetail)
const detailRef = ref()

function goBack() {
  router.back()
}

function handleSave() {
  try {
    taskDetailForm.detail = detailRef.value?.getForm?.()
    if (!taskDetailForm.detail) {
      proxy.$modal.msgError('表单未就绪')
      return
    }
      proxy.$modal.msgSuccess('已暂存任务配置')
    
    console.log('sync task payload', taskDetailForm)
  } catch (e) {
    proxy.$modal.msgError('保存失败')
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

</script>

<style scoped>
</style>

