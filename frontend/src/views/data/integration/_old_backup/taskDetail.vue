<template>
  <div class="app-container">
    <el-card>
      <div class="header-actions">
        <el-form :inline="true" :model="taskForm" class="demo-form-inline">
          <el-form-item label="任务名称">
            <el-input v-model="taskForm.name" placeholder="请输入任务名称" style="width: 280px" />
          </el-form-item>
          <el-form-item label="任务类型">
            <el-select v-model="taskForm.type" placeholder="请选择任务类型" style="width: 200px">
              <el-option label="数据库→数据库" value="dbToDb" />
              <el-option label="数据库→Hive" value="dbToHive" />
              <el-option label="Hive→数据库" value="hiveToDb" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button @click="goBack">返回列表</el-button>
            <el-button type="primary" @click="handleSave">保 存</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 基础配置 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <span>基础配置</span>
      </template>
      <el-form :model="taskForm" label-width="140px">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="目标层级">
              <el-select v-model="taskForm.targetLayer" placeholder="请选择目标层级" style="width: 100%">
                <el-option label="STG缓冲层" value="stg" />
                <el-option label="ODS原始层" value="ods" />
                <el-option label="DWD明细层" value="dwd" />
                <el-option label="DWS汇总层" value="dws" />
                <el-option label="ADS应用层" value="ads" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="执行器类型">
              <el-select v-model="taskForm.executorType" placeholder="请选择执行器" style="width: 100%">
                <el-option label="DataX执行器" value="datax" />
                <el-option label="Spark SQL执行器" value="spark_sql" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="状态">
              <el-radio-group v-model="taskForm.status">
                <el-radio label="0">正常</el-radio>
                <el-radio label="1">停用</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="备注">
              <el-input v-model="taskForm.remark" type="textarea" :rows="1" placeholder="请输入备注" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>
        <span>数据源配置</span>
      </template>
      <SyncConfigDetail v-model:detail="taskForm.detail" />

      <!-- 多租户采集配置 -->
      <el-divider content-position="left">多租户采集优化（5000+租户场景）</el-divider>
      <el-form :model="taskForm" label-width="180px">
        <el-form-item label="是否多库采集任务">
          <el-switch v-model="taskForm.isMultiDbTask" active-text="是" inactive-text="否" />
          <el-tooltip content="开启后可在单个DataX任务中采集同一数据源下的多个租户库，适合5000+租户场景" placement="top">
            <el-icon style="margin-left: 8px; cursor: help"><QuestionFilled /></el-icon>
          </el-tooltip>
        </el-form-item>
        <el-form-item v-if="taskForm.isMultiDbTask" label="源数据库列表">
          <el-select
            v-model="taskForm.sourceDatabases"
            multiple
            filterable
            allow-create
            placeholder="请输入数据库名，可添加多个（如：tenant_db_001, tenant_db_002）"
            style="width: 100%"
          >
            <template #footer>
              <el-button text @click="taskForm.sourceDatabases = []">清空</el-button>
            </template>
          </el-select>
          <div style="margin-top: 8px; color: #909399; font-size: 12px">
            已选择 {{ taskForm.sourceDatabases?.length || 0 }} 个数据库
          </div>
        </el-form-item>
        <el-form-item v-if="taskForm.isMultiDbTask" label="租户ID字段">
          <el-input
            v-model="taskForm.tenantIdField"
            placeholder="用于标识租户的字段名，如：tenant_id"
            style="width: 300px"
          />
          <span style="margin-left: 12px; color: #909399; font-size: 12px">留空则从数据库名提取</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 增量策略与执行配置 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <span>增量策略与执行配置</span>
      </template>
      <el-form :model="taskForm" label-width="160px">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="增量策略">
              <el-select v-model="taskForm.incrementalStrategy" placeholder="请选择增量策略" style="width: 100%">
                <el-option label="全量同步" value="full" />
                <el-option label="按新增时间增量" value="incremental_addtime" />
                <el-option label="按更新时间增量" value="incremental_updatetime" />
                <el-option label="按自增ID增量" value="incremental_id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item v-if="taskForm.incrementalStrategy !== 'full'" label="增量字段">
              <el-input v-model="taskForm.incrementalField" placeholder="如：create_time, update_time, id" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="批处理大小">
              <el-input-number v-model="taskForm.batchSize" :min="1000" :max="100000" :step="1000" style="width: 200px" />
              <span style="margin-left: 12px; color: #909399; font-size: 12px">行/批次</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="并发度">
              <el-input-number v-model="taskForm.concurrency" :min="1" :max="50" style="width: 200px" />
              <span style="margin-left: 12px; color: #909399; font-size: 12px">多库采集时生效</span>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
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

<script setup name="DataIntegrationTaskDetail">
import { reactive, ref, watch, onMounted, getCurrentInstance } from 'vue'
import Crontab from '@/components/Crontab'
import SyncConfigDetail from './components/SyncConfigDetail'
import { useRoute, useRouter } from 'vue-router'
import { addTask, updateTask, getTask, listTasks } from '@/api/data/integration'
import useTagsViewStore from '@/store/modules/tagsView'
import { QuestionFilled } from '@element-plus/icons-vue'

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
  targetLayer: '',
  executorType: 'datax',
  status: '0',
  remark: '',
  detail: {},
  // 多租户字段
  isMultiDbTask: false,
  sourceDatabases: [],
  tenantIdField: '',
  // 增量策略
  incrementalStrategy: 'full',
  incrementalField: '',
  // 执行配置
  batchSize: 10000,
  concurrency: 1,
  // 调度配置
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
  if (!taskForm.targetLayer) {
    proxy.$modal.msgError('请选择目标层级')
    return
  }
  if (!taskForm.executorType) {
    proxy.$modal.msgError('请选择执行器类型')
    return
  }
  if (taskForm.schedule?.type === 'cron' && !taskForm.schedule?.cronExpr) {
    proxy.$modal.msgError('请输入cron表达式')
    return
  }

  try {
    const schedule = { ...(taskForm.schedule || {}) }
    if (schedule.type !== 'cron') schedule.cronExpr = ''

    // 构建payload，映射前端字段到后端字段名
    const payload = {
      taskName: taskForm.name,
      taskType: taskForm.type,
      targetLayer: taskForm.targetLayer,
      executorType: taskForm.executorType,
      status: taskForm.status,
      remark: taskForm.remark,
      schedule,
      detail: taskForm.detail,
      // 多租户字段
      isMultiDbTask: taskForm.isMultiDbTask,
      sourceDatabases: taskForm.sourceDatabases || [],
      tenantIdField: taskForm.tenantIdField || '',
      // 增量策略
      incrementalStrategy: taskForm.incrementalStrategy,
      incrementalField: taskForm.incrementalField || '',
      // 执行配置
      batchSize: taskForm.batchSize || 10000,
      concurrency: taskForm.concurrency || 1,
    }

    const id = route.params.id
    if (id && id !== 'new') {
      await updateTask(id, payload)
      proxy.$modal.msgSuccess('保存成功')
    } else {
      await addTask(payload)
      proxy.$modal.msgSuccess('新增成功')
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
  taskForm.type = route.query.type || 'dbToDb'
  await loadScheduleGroups()
  if (id && id !== 'new') {
    getTask(id).then(res => {
      const data = res.data || {}
      taskForm.type = data.taskType || taskForm.type
      taskForm.name = data.taskName || ''
      taskForm.targetLayer = data.targetLayer || ''
      taskForm.executorType = data.executorType || 'datax'
      taskForm.status = data.status || '0'
      taskForm.remark = data.remark || ''
      taskForm.schedule = data.schedule || { type: 'manual', cronExpr: '', group: '' }
      taskForm.detail = data.detail || {}
      // 多租户字段
      taskForm.isMultiDbTask = data.isMultiDbTask || false
      taskForm.sourceDatabases = data.sourceDatabases || []
      taskForm.tenantIdField = data.tenantIdField || ''
      // 增量策略
      taskForm.incrementalStrategy = data.incrementalStrategy || 'full'
      taskForm.incrementalField = data.incrementalField || ''
      // 执行配置
      taskForm.batchSize = data.batchSize || 10000
      taskForm.concurrency = data.concurrency || 1
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
