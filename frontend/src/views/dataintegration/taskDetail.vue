<template>
  <div class="app-container">
      <el-form>
        <el-form-item label="任务名称">
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" style="width: 320px" />
        </el-form-item>
      </el-form>

    <el-card>
        <template #header>
            <span>任务配置</span>
        </template>
        <el-row>
            <el-col :span="12">
            <el-card>
                <template #header>
                    <span>来源</span>
                </template>
            </el-card>
            </el-col>
            <el-col :span="12">
            <el-card>
                <template #header>
                    <span>目标</span>
                </template>
            </el-card>
            </el-col>
        </el-row>
    </el-card>

    <el-card>
        <field-mapping 
            v-model:source-columns="taskForm.detail.sourceColumns"
            v-model:target-columns="taskForm.detail.targetColumns"
            v-model:mappings="taskForm.detail.mappings"
            v-model:defaultMapping="taskForm.detail.defaultMapping"
        />
    </el-card>

    <!-- <el-card style="margin-top: 16px">
        <template #header>
            <span>同步配置</span>
        </template>
        <el-form :model="taskForm" label-width="120px">
            <el-form-item label="where条件">
                <el-input v-model="taskForm.detail.where" type="textarea" :rows="2" placeholder="示例：status = 1" />
            </el-form-item>
            <el-form-item label="同步方式">
                <el-radio-group v-model="taskForm.detail.mode.type">
                    <el-radio label="full">全量</el-radio>
                    <el-radio label="incremental">增量</el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item v-if="taskForm.detail.mode.type === 'incremental'" label="增量字段">
                <el-select v-model="taskForm.detail.mode.incrementField" filterable allow-create placeholder="选择或输入增量字段"
                    style="width: 240px">
                    <el-option v-for="c in taskForm.detail.sourceColumns" :key="c" :label="c" :value="c" />
                </el-select>
                <el-select v-model="taskForm.detail.mode.incrementType" style="width: 180px; margin-left: 12px">
                    <el-option label="自增ID" value="id" />
                    <el-option label="时间戳" value="timestamp" />
                    <el-option label="自定义" value="custom" />
                </el-select>
            </el-form-item>
        </el-form>
    </el-card> -->

    <!-- 调度配置 -->
    <el-card style="margin-top: 16px">
        <template #header>
        <span>任务调度策略</span>
        </template>
        <el-form :model="taskForm" label-width="120px">
        <el-form-item label="调度策略">
        <el-radio-group v-model="taskForm.schedule.type">
            <el-radio label="manual">手动</el-radio>
            <el-radio label="cron">定时</el-radio>
        </el-radio-group>
        <div v-if="taskForm.schedule.type==='cron'" style="display: inline-flex; align-items: center; margin-left: 12px">
            <el-input v-model="taskForm.schedule.cronExpr" placeholder="cron表达式" style="width: 240px" />
            <el-button style="margin-left: 8px" @click="handleShowCron">生成</el-button>
        </div>
        </el-form-item>
        <el-form-item label="分组调度">
            <el-select v-model="taskForm.schedule.group" allow-create filterable default-first-option placeholder="请选择分组" style="width: 240px">
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
import FieldMapping from '@/components/FieldMapping'
import { useRoute, useRouter } from 'vue-router'
import { addTask, updateTask, getTask } from '@/api/dataintegration'
const route = useRoute()
const router = useRouter()
const { proxy } = getCurrentInstance()

function goBack() {
  router.back()
}

const taskForm = reactive({
  name: '',
  type: 'db2db',
  schedule: {
    type: 'manual',
    cronExpr: '',
    group: '',
  },
  detail: {}
})

async function handleSave() {
  try {
    const payload = {
      taskName: taskForm.name,
      taskType: taskForm.type,
      schedule: taskForm.schedule,
      detail: taskForm.detail
    }
    const id = route.params.id
    if (id && id !== 'new') {
      await updateTask(id, payload)
      proxy.$modal.msgSuccess('保存成功')
    } else {
      await addTask(payload)
      router.push({ name: 'DataIntegrationTasks' })
    }
  } catch (e) {
    console.log(e)
  }
}

const handleValidate = () => { }

// 任务调度信息


const scheduleGroups = ref([])
const openCron = ref(false)
const expression = ref('')

function handleShowCron() {
  expression.value = taskForm.schedule.cronExpr
  openCron.value = true
}

function crontabFill(value) {
  taskForm.schedule.cronExpr = value
}

const detailRef = ref()

onMounted(() => {
  const id = route.params.id
  if (id && id !== 'new') {
    getTask(id).then(res => {
      const data = res.data || {}
      taskForm.type = data.taskType || taskForm.type
      taskForm.name = data.taskName || ''
      taskForm.schedule = data.schedule || { type: 'manual', cronExpr: '', group: '' }
      taskForm.detail = data.detail || {}
    })
  }
})

</script>

<style scoped>
</style>

