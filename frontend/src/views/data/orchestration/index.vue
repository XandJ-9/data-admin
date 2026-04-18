<template>
  <div class="app-container orchestration-workbench" v-loading="taskLoading || dependencyLoading">
    <el-card shadow="hover" class="hero-panel">
      <div class="hero-copy">
        <div>
          <span class="hero-eyebrow">任务编排</span>
          <h1>用任务卡片和依赖泳道串起同步任务与 SQL 任务</h1>
          <p>
            当前阶段先落最小 DAG 编排工作台：左侧选择任务，右侧查看它的上游/下游依赖，并通过抽屉维护依赖边，为后续调度器自动触发打基础。
          </p>
          <div class="hero-actions">
            <el-button type="primary" :icon="Plus" @click="handleAdd" v-hasPermi="['datatask:dependency:add']">新增依赖</el-button>
            <el-button text type="primary" :icon="Refresh" @click="reloadWorkbench">刷新编排视图</el-button>
          </div>
        </div>
        <div class="hero-aside">
          <div class="highlight-card">
            <span class="highlight-label">本页价值</span>
            <ul>
              <li>让数据集成任务和 SQL 任务形成真实依赖链</li>
              <li>直接观察某个任务的上下游关系，而不是只看一张依赖表</li>
              <li>让“任务配置”与“编排关系”成为两个不同的工作面</li>
            </ul>
          </div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="metric-row">
      <el-col v-for="item in overviewCards" :key="item.title" :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" :class="item.tone">
            <el-icon><component :is="item.icon" /></el-icon>
          </div>
          <div class="metric-body">
            <span class="metric-label">{{ item.title }}</span>
            <strong class="metric-value">{{ item.value }}</strong>
            <span class="metric-hint">{{ item.hint }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="workspace-row">
      <el-col :xs="24" :xl="8">
        <el-card shadow="hover" class="rail-card filter-card">
          <template #header>
            <div class="section-head">
              <div>
                <h3>任务筛选</h3>
                <p>先锁定当前要观察或配置编排关系的任务。</p>
              </div>
            </div>
          </template>

          <div class="filter-group">
            <el-input
              v-model="taskQueryParams.taskName"
              placeholder="搜索任务名称"
              clearable
              @keyup.enter="handleTaskQuery"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="filter-group">
            <span class="filter-label">任务类型</span>
            <el-radio-group v-model="taskQueryParams.taskType" size="small" @change="handleTaskQuery">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="DATA_SYNC">数据同步</el-radio-button>
              <el-radio-button label="SQL_COMPUTE">SQL 计算</el-radio-button>
            </el-radio-group>
          </div>

          <div class="filter-actions">
            <el-button type="primary" :icon="Search" @click="handleTaskQuery">应用筛选</el-button>
            <el-button :icon="Refresh" @click="resetTaskQuery">重置</el-button>
          </div>
        </el-card>

        <el-card shadow="hover" class="rail-card task-rail-card">
          <template #header>
            <div class="section-head">
              <div>
                <h3>统一任务清单</h3>
                <p>点击任务卡片，右侧查看它的上下游依赖泳道。</p>
              </div>
              <span class="section-meta">共 {{ taskTotal }} 条</span>
            </div>
          </template>

          <el-scrollbar max-height="760px">
            <div v-if="taskList.length" class="task-rail">
              <article
                v-for="task in taskList"
                :key="task.taskId"
                class="task-card"
                :class="{ active: selectedTask?.taskId === task.taskId }"
                @click="selectTask(task)"
              >
                <div class="task-card-top">
                  <div>
                    <h4>{{ task.taskName }}</h4>
                    <p>{{ task.taskCode }}</p>
                  </div>
                  <el-tag :type="task.taskType === 'DATA_SYNC' ? 'success' : 'primary'" size="small" effect="plain">
                    {{ taskTypeLabel(task.taskType) }}
                  </el-tag>
                </div>
                <div class="task-card-meta">
                  <span>调度方式：{{ scheduleTypeLabel(task.scheduleType) }}</span>
                  <span>负责人：{{ task.owner || '-' }}</span>
                </div>
                <div class="task-card-footer">
                  <el-tag v-if="task.lastInstanceStatus" :type="instanceStatusTagType(task.lastInstanceStatus)" size="small">
                    {{ instanceStatusLabel(task.lastInstanceStatus) }}
                  </el-tag>
                  <small>{{ task.lastInstanceAt || '暂无运行记录' }}</small>
                </div>
              </article>
            </div>
            <el-empty v-else description="暂无匹配任务" :image-size="68" />
          </el-scrollbar>

          <pagination
            v-show="taskTotal > 0"
            :total="taskTotal"
            v-model:page="taskQueryParams.pageNum"
            v-model:limit="taskQueryParams.pageSize"
            @pagination="loadTasks"
          />
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="16">
        <template v-if="selectedTask">
          <el-card shadow="hover" class="detail-hero-card">
            <div class="detail-hero">
              <div class="detail-main">
                <div class="detail-title-row">
                  <div>
                    <span class="detail-eyebrow">{{ selectedTask.taskCode }}</span>
                    <h2>{{ selectedTask.taskName }}</h2>
                  </div>
                  <div class="detail-tags">
                    <el-tag :type="selectedTask.taskType === 'DATA_SYNC' ? 'success' : 'primary'">
                      {{ taskTypeLabel(selectedTask.taskType) }}
                    </el-tag>
                    <el-tag effect="plain">{{ scheduleTypeLabel(selectedTask.scheduleType) }}</el-tag>
                  </div>
                </div>
                <p class="detail-description">
                  {{ selectedTask.remark || '当前任务已纳入统一任务中心，可与其他同步任务或 SQL 任务形成依赖关系。' }}
                </p>
              </div>
              <div class="detail-actions">
                <el-button type="primary" :icon="Top" @click="handleAddUpstream" v-hasPermi="['datatask:dependency:add']">添加上游</el-button>
                <el-button type="primary" plain :icon="Bottom" @click="handleAddDownstream" v-hasPermi="['datatask:dependency:add']">添加下游</el-button>
              </div>
            </div>
          </el-card>

          <el-row :gutter="16" class="lane-row">
            <el-col :xs="24" :xl="12">
              <el-card shadow="hover" class="lane-card">
                <template #header>
                  <div class="section-head">
                    <div>
                      <h3>上游泳道</h3>
                      <p>谁先成功，当前任务才会被触发。</p>
                    </div>
                    <span class="section-meta">{{ upstreamDependencies.length }} 条</span>
                  </div>
                </template>

                <div v-if="upstreamDependencies.length" class="dependency-lane">
                  <article v-for="edge in upstreamDependencies" :key="edge.dependencyId" class="dependency-card upstream">
                    <div class="dependency-main">
                      <span class="dependency-label">上游任务</span>
                      <h4>{{ edge.upstreamTaskName }}</h4>
                      <p>{{ edge.upstreamTaskCode }}</p>
                    </div>
                    <div class="dependency-meta">
                      <el-tag size="small" type="success" effect="plain">成功触发</el-tag>
                      <span>延迟 {{ edge.lagSeconds }}s</span>
                    </div>
                    <div class="dependency-actions">
                      <el-button link type="primary" :icon="Edit" @click="handleUpdate(edge)" v-hasPermi="['datatask:dependency:edit']">修改</el-button>
                      <el-button link type="danger" :icon="Delete" @click="handleDelete(edge)" v-hasPermi="['datatask:dependency:remove']">删除</el-button>
                    </div>
                  </article>
                </div>
                <el-empty v-else description="暂无上游依赖" :image-size="72" />
              </el-card>
            </el-col>

            <el-col :xs="24" :xl="12">
              <el-card shadow="hover" class="lane-card">
                <template #header>
                  <div class="section-head">
                    <div>
                      <h3>下游泳道</h3>
                      <p>当前任务成功后，会推动哪些任务继续执行。</p>
                    </div>
                    <span class="section-meta">{{ downstreamDependencies.length }} 条</span>
                  </div>
                </template>

                <div v-if="downstreamDependencies.length" class="dependency-lane">
                  <article v-for="edge in downstreamDependencies" :key="edge.dependencyId" class="dependency-card downstream">
                    <div class="dependency-main">
                      <span class="dependency-label">下游任务</span>
                      <h4>{{ edge.downstreamTaskName }}</h4>
                      <p>{{ edge.downstreamTaskCode }}</p>
                    </div>
                    <div class="dependency-meta">
                      <el-tag size="small" type="primary" effect="plain">成功触发</el-tag>
                      <span>延迟 {{ edge.lagSeconds }}s</span>
                    </div>
                    <div class="dependency-actions">
                      <el-button link type="primary" :icon="Edit" @click="handleUpdate(edge)" v-hasPermi="['datatask:dependency:edit']">修改</el-button>
                      <el-button link type="danger" :icon="Delete" @click="handleDelete(edge)" v-hasPermi="['datatask:dependency:remove']">删除</el-button>
                    </div>
                  </article>
                </div>
                <el-empty v-else description="暂无下游依赖" :image-size="72" />
              </el-card>
            </el-col>
          </el-row>

          <el-card shadow="hover" class="content-card summary-card">
            <template #header>
              <div class="section-head">
                <div>
                  <h3>编排摘要</h3>
                  <p>把当前任务在 DAG 中的位置用更直观的文字总结出来。</p>
                </div>
              </div>
            </template>
            <div class="summary-grid">
              <article class="summary-item">
                <span class="summary-label">当前角色</span>
                <strong>{{ selectedTask.taskType === 'DATA_SYNC' ? '同步源任务' : '计算任务' }}</strong>
                <p>{{ scheduleTypeLabel(selectedTask.scheduleType) }}，{{ selectedTask.owner || '未指定负责人' }}</p>
              </article>
              <article class="summary-item">
                <span class="summary-label">上游数量</span>
                <strong>{{ upstreamDependencies.length }}</strong>
                <p>上游越多，越适合后续接成依赖触发或批次编排。</p>
              </article>
              <article class="summary-item">
                <span class="summary-label">下游数量</span>
                <strong>{{ downstreamDependencies.length }}</strong>
                <p>下游越多，这个任务越可能是链路上的关键节点。</p>
              </article>
            </div>
          </el-card>
        </template>

        <el-card v-else shadow="hover" class="empty-workspace-card">
          <el-empty description="左侧选择一个统一任务，右侧查看它的依赖泳道" :image-size="88" />
        </el-card>
      </el-col>
    </el-row>

    <el-drawer
      v-model="open"
      :title="title"
      size="620px"
      append-to-body
      :close-on-click-modal="false"
      class="dependency-drawer"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="drawer-form">
        <el-card shadow="never" class="drawer-section">
          <template #header><span>依赖边配置</span></template>
          <el-form-item label="上游任务" prop="upstreamTaskId">
            <el-select v-model="form.upstreamTaskId" filterable placeholder="请选择上游任务">
              <el-option
                v-for="item in taskOptions"
                :key="item.taskId"
                :label="`${item.taskName}（${taskTypeLabel(item.taskType)}）`"
                :value="item.taskId"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="下游任务" prop="downstreamTaskId">
            <el-select v-model="form.downstreamTaskId" filterable placeholder="请选择下游任务">
              <el-option
                v-for="item in taskOptions"
                :key="item.taskId"
                :label="`${item.taskName}（${taskTypeLabel(item.taskType)}）`"
                :value="item.taskId"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="触发条件" prop="triggerCondition">
            <el-select v-model="form.triggerCondition" disabled>
              <el-option label="上游成功" value="SUCCESS" />
            </el-select>
          </el-form-item>
          <el-form-item label="延迟秒数" prop="lagSeconds">
            <el-input-number v-model="form.lagSeconds" :min="0" :max="86400" controls-position="right" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="说明这条依赖为什么存在，例如“同步成功后才能汇总”。" />
          </el-form-item>
        </el-card>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="open = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">保存依赖</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup name="DataOrchestration">
import { Bottom, CircleCheck, Connection, DataAnalysis, Delete, Edit, Link, Plus, Refresh, Search, Top } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  addTaskDependency,
  delTaskDependency,
  listTaskDependencies,
  listTasks,
  updateTaskDependency,
} from '@/api/data/datatask'

const taskLoading = ref(false)
const dependencyLoading = ref(false)
const submitting = ref(false)
const open = ref(false)
const title = ref('')
const formRef = ref()
const taskList = ref([])
const taskTotal = ref(0)
const taskOptions = ref([])
const dependencyList = ref([])
const selectedTask = ref(null)
let taskOptionsRequestToken = 0
let taskListRequestToken = 0

const taskQueryParams = ref({
  pageNum: 1,
  pageSize: 10,
  taskName: '',
  taskType: '',
})

const form = ref(createDefaultForm())

const rules = {
  upstreamTaskId: [{ required: true, message: '请选择上游任务', trigger: 'change' }],
  downstreamTaskId: [{ required: true, message: '请选择下游任务', trigger: 'change' }],
}

const overviewCards = computed(() => [
  {
    title: '当前任务数',
    value: taskTotal.value,
    hint: '当前筛选条件下可见的统一任务总量',
    icon: Connection,
    tone: 'tone-blue',
  },
  {
    title: '依赖边数量',
    value: dependencyList.value.length,
    hint: '已配置的任务依赖关系总量',
    icon: Link,
    tone: 'tone-green',
  },
  {
    title: '同步任务',
    value: taskList.value.filter(item => item.taskType === 'DATA_SYNC').length,
    hint: '当前列表中的数据同步任务数量',
    icon: DataAnalysis,
    tone: 'tone-orange',
  },
  {
    title: '已进入依赖触发',
    value: taskList.value.filter(item => item.scheduleType === 'dependency').length,
    hint: '当前列表中已被依赖驱动的任务数量',
    icon: CircleCheck,
    tone: 'tone-violet',
  },
])

const upstreamDependencies = computed(() => {
  if (!selectedTask.value) {
    return []
  }
  return dependencyList.value.filter(item => item.downstreamTaskId === selectedTask.value.taskId)
})

const downstreamDependencies = computed(() => {
  if (!selectedTask.value) {
    return []
  }
  return dependencyList.value.filter(item => item.upstreamTaskId === selectedTask.value.taskId)
})

function createDefaultForm() {
  return {
    dependencyId: null,
    upstreamTaskId: null,
    downstreamTaskId: null,
    triggerCondition: 'SUCCESS',
    lagSeconds: 0,
    remark: '',
  }
}

function getErrorMessage(error, fallback = '请求失败，请稍后重试') {
  return error?.response?.data?.msg || error?.response?.data?.message || error?.message || fallback
}

function syncSelectedTask() {
  const currentId = selectedTask.value?.taskId
  selectedTask.value = taskList.value.find(item => item.taskId === currentId) || taskList.value[0] || null
}

async function loadTasks() {
  const currentToken = ++taskListRequestToken
  taskLoading.value = true
  try {
    const res = await listTasks(taskQueryParams.value)
    if (currentToken !== taskListRequestToken) {
      return
    }
    taskList.value = res.rows || []
    taskTotal.value = res.total || 0
    syncSelectedTask()
  } catch (error) {
    if (currentToken === taskListRequestToken) {
      taskList.value = []
      taskTotal.value = 0
      selectedTask.value = null
      ElMessage.error(getErrorMessage(error, '加载任务清单失败'))
    }
  } finally {
    if (currentToken === taskListRequestToken) {
      taskLoading.value = false
    }
  }
}

async function loadTaskOptions() {
  const currentToken = ++taskOptionsRequestToken
  const pageSize = 100
  let pageNum = 1
  let total = 0
  const rows = []
  try {
    do {
      const res = await listTasks({ pageNum, pageSize })
      total = res.total || 0
      rows.push(...(res.rows || []))
      pageNum += 1
    } while (rows.length < total)
    if (currentToken === taskOptionsRequestToken) {
      taskOptions.value = rows
    }
  } catch (error) {
    if (currentToken === taskOptionsRequestToken) {
      taskOptions.value = []
      ElMessage.error(getErrorMessage(error, '加载任务选项失败'))
    }
  }
}

async function loadDependencies() {
  dependencyLoading.value = true
  try {
    const res = await listTaskDependencies({})
    dependencyList.value = res.rows || []
  } catch (error) {
    dependencyList.value = []
    ElMessage.error(getErrorMessage(error, '加载依赖关系失败'))
  } finally {
    dependencyLoading.value = false
  }
}

function reloadWorkbench() {
  loadTaskOptions()
  loadTasks()
  loadDependencies()
}

function selectTask(task) {
  selectedTask.value = task
}

function handleTaskQuery() {
  taskQueryParams.value.pageNum = 1
  loadTasks()
}

function resetTaskQuery() {
  taskQueryParams.value = {
    pageNum: 1,
    pageSize: 10,
    taskName: '',
    taskType: '',
  }
  loadTasks()
}

function handleAdd() {
  form.value = createDefaultForm()
  formRef.value?.clearValidate()
  title.value = '新增依赖关系'
  open.value = true
}

function handleAddUpstream() {
  form.value = {
    ...createDefaultForm(),
    downstreamTaskId: selectedTask.value?.taskId || null,
  }
  formRef.value?.clearValidate()
  title.value = '为当前任务添加上游'
  open.value = true
}

function handleAddDownstream() {
  form.value = {
    ...createDefaultForm(),
    upstreamTaskId: selectedTask.value?.taskId || null,
  }
  formRef.value?.clearValidate()
  title.value = '为当前任务添加下游'
  open.value = true
}

function handleUpdate(row) {
  form.value = {
    dependencyId: row.dependencyId,
    upstreamTaskId: row.upstreamTaskId,
    downstreamTaskId: row.downstreamTaskId,
    triggerCondition: row.triggerCondition,
    lagSeconds: row.lagSeconds,
    remark: row.remark || '',
  }
  formRef.value?.clearValidate()
  title.value = '修改依赖关系'
  open.value = true
}

function handleDelete(row) {
  ElMessageBox.confirm(`确认删除依赖「${row.upstreamTaskName} → ${row.downstreamTaskName}」吗？`, '提示', {
    type: 'warning',
  }).then(() => {
    return delTaskDependency(row.dependencyId)
  }).then(() => {
    ElMessage.success('删除成功')
    reloadWorkbench()
  }).catch(() => {})
}

async function submitForm() {
  try {
    await formRef.value.validate()
    submitting.value = true
    if (form.value.dependencyId) {
      await updateTaskDependency(form.value)
    } else {
      const payload = { ...form.value }
      delete payload.dependencyId
      await addTaskDependency(payload)
    }
    ElMessage.success('保存成功')
    open.value = false
    reloadWorkbench()
  } catch (error) {
    if (error?.response || error instanceof Error) {
      ElMessage.error(getErrorMessage(error, '保存依赖失败'))
    }
  } finally {
    submitting.value = false
  }
}

function taskTypeLabel(value) {
  return value === 'DATA_SYNC' ? '数据同步' : 'SQL计算'
}

function scheduleTypeLabel(value) {
  const mapping = {
    manual: '手动',
    cron: 'Cron',
    dependency: '依赖触发',
  }
  return mapping[value] || value || '-'
}

function instanceStatusLabel(value) {
  const mapping = {
    pending: '等待执行',
    running: '执行中',
    success: '执行成功',
    failed: '执行失败',
    cancelled: '已取消',
  }
  return mapping[value] || '-'
}

function instanceStatusTagType(value) {
  const mapping = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    cancelled: 'info',
  }
  return mapping[value] || 'info'
}

onMounted(() => {
  reloadWorkbench()
})
</script>

<style scoped>
.hero-panel,
.metric-card,
.rail-card,
.detail-hero-card,
.lane-card,
.summary-card,
.empty-workspace-card {
  border-radius: 16px;
}

.hero-panel {
  margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.08), rgba(124, 77, 255, 0.06));
}

.hero-copy {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(260px, 0.9fr);
  gap: 20px;
}

.hero-eyebrow {
  color: var(--el-color-primary);
  font-size: 13px;
  font-weight: 600;
}

.hero-copy h1 {
  margin: 8px 0 10px;
  font-size: 28px;
  line-height: 1.3;
}

.hero-copy p,
.section-head p,
.detail-description,
.summary-item p {
  margin: 0;
  color: var(--el-text-color-regular);
  line-height: 1.7;
}

.hero-actions,
.filter-actions,
.detail-actions,
.dependency-actions,
.drawer-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.highlight-card {
  height: 100%;
  padding: 18px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: inset 0 0 0 1px rgba(64, 158, 255, 0.08);
}

.highlight-label,
.filter-label,
.metric-label,
.metric-hint,
.section-meta,
.dependency-label,
.detail-eyebrow,
.summary-label {
  color: var(--el-text-color-secondary);
}

.highlight-card ul {
  margin: 10px 0 0;
  padding-left: 18px;
  line-height: 1.8;
}

.metric-row,
.workspace-row,
.lane-row {
  margin-top: 16px;
}

.metric-card {
  display: flex;
  gap: 14px;
  align-items: center;
}

.metric-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  font-size: 20px;
}

.metric-icon.tone-blue {
  color: #2f7df6;
  background: rgba(47, 125, 246, 0.12);
}

.metric-icon.tone-green {
  color: #28a745;
  background: rgba(40, 167, 69, 0.12);
}

.metric-icon.tone-orange {
  color: #ff8f1f;
  background: rgba(255, 143, 31, 0.14);
}

.metric-icon.tone-violet {
  color: #7c4dff;
  background: rgba(124, 77, 255, 0.12);
}

.metric-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-value {
  font-size: 26px;
  line-height: 1;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.section-head h3,
.task-card-top h4,
.detail-title-row h2,
.dependency-main h4 {
  margin: 0;
}

.task-rail,
.dependency-lane,
.summary-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card,
.dependency-card,
.summary-item {
  padding: 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 14px;
  background: var(--el-bg-color);
}

.task-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.task-card:hover,
.task-card.active {
  border-color: rgba(64, 158, 255, 0.55);
  box-shadow: 0 10px 24px rgba(31, 35, 41, 0.08);
}

.task-card-top,
.task-card-footer,
.detail-title-row,
.detail-hero,
.dependency-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.task-card-top p,
.task-card-meta,
.task-card-footer small,
.dependency-main p {
  margin: 4px 0 0;
  color: var(--el-text-color-secondary);
}

.task-card-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 12px 0;
}

.detail-hero {
  align-items: center;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.lane-card,
.summary-card {
  height: 100%;
}

.dependency-card.upstream {
  border-left: 4px solid rgba(103, 194, 58, 0.8);
}

.dependency-card.downstream {
  border-left: 4px solid rgba(64, 158, 255, 0.8);
}

.dependency-main {
  margin-bottom: 12px;
}

.dependency-meta {
  align-items: center;
  margin-bottom: 10px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.summary-item strong {
  display: block;
  margin: 8px 0 6px;
  font-size: 28px;
}

.drawer-section {
  margin-bottom: 16px;
  border-radius: 14px;
}

.drawer-section :deep(.el-card__header) {
  padding: 16px 20px;
  font-weight: 600;
}

@media (max-width: 1200px) {
  .hero-copy,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .detail-hero {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 768px) {
  .hero-copy h1 {
    font-size: 24px;
  }

  .task-card-top,
  .task-card-footer,
  .detail-title-row,
  .dependency-meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
