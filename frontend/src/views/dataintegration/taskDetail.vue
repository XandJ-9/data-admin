<template>
  <div class="app-container">
    <div style="display:flex; justify-content: space-between; align-items:center;">
      <h3 style="margin:0;">同步任务详情</h3>
      <div>
        <el-button @click="goList">返回列表</el-button>
        <el-button type="primary" @click="saveTask">保存任务</el-button>
        <el-button type="success" @click="startTask">启动</el-button>
        <el-button type="warning" @click="pauseTask">暂停</el-button>
      </div>
    </div>

    <el-form ref="formRef" :model="form" label-width="140px" style="margin-top: 12px;">
      <el-card shadow="never" class="card-box">
        <template #header>基础信息</template>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入任务名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="同步类型" prop="syncType">
              <el-select v-model="form.syncType" placeholder="请选择">
                <el-option label="数据库 → 数据库" value="dbToDb" />
                <el-option label="数据库 → 集群" value="dbToCluster" />
                <el-option label="集群 → 数据库" value="clusterToDb" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="同步范围" prop="scope">
              <el-select v-model="form.scope" placeholder="请选择">
                <el-option label="单表同步" value="single" />
                <el-option label="整库同步" value="full" />
                <el-option label="分库分表同步" value="sharded" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="never" class="card-box" style="margin-top: 12px;">
        <template #header>源端配置</template>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="源类型">
              <el-select v-model="sourceType" @change="onSourceTypeChange">
                <el-option label="数据库" value="database" />
                <el-option label="集群" value="cluster" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据源">
              <el-select v-model="form.sourceDsId" filterable placeholder="选择数据源" @change="loadSourceDatabases">
                <el-option v-for="ds in sourceOptions" :key="ds.id" :label="ds.name" :value="ds.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="选择数据库(可多选)">
              <el-select v-model="form.sourceDatabases" multiple filterable placeholder="选择数据库">
                <el-option v-for="db in sourceDbOptions" :key="db" :label="db" :value="db" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="never" class="card-box" style="margin-top: 12px;">
        <template #header>目标端配置</template>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="目标类型">
              <el-select v-model="targetType" @change="onTargetTypeChange">
                <el-option label="数据库" value="database" />
                <el-option label="集群" value="cluster" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据源">
              <el-select v-model="form.targetDsId" filterable placeholder="选择数据源" @change="loadTargetDatabases">
                <el-option v-for="ds in targetOptions" :key="ds.id" :label="ds.name" :value="ds.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="选择数据库">
              <el-select v-model="form.targetDatabase" filterable placeholder="选择数据库">
                <el-option v-for="db in targetDbOptions" :key="db" :label="db" :value="db" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="never" class="card-box" style="margin-top: 12px;">
        <template #header>同步范围配置</template>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="范围类型">
              <el-radio-group v-model="form.range.type">
                <el-radio label="all">同步所有表</el-radio>
                <el-radio label="tables">指定部分表</el-radio>
                <el-radio label="sharded">分库分表</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="form.range.type === 'tables'">
            <el-form-item label="表名列表">
              <el-select v-model="form.range.tables" multiple filterable placeholder="选择需要同步的表">
                <el-option v-for="t in tableOptions" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="form.range.type === 'sharded'">
            <el-form-item label="分片规则">
              <el-input v-model="form.range.shardRule" placeholder="例如：order_${yyyyMM} 或 user_${00..63}" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="never" class="card-box" style="margin-top: 12px;">
        <template #header>同步方式与频率</template>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="同步方式">
              <el-radio-group v-model="form.mode">
                <el-radio label="incremental">增量同步</el-radio>
                <el-radio label="full">全量同步</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="触发方式">
              <el-radio-group v-model="form.frequencyType">
                <el-radio label="manual">手动触发</el-radio>
                <el-radio label="cron">定时任务</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="form.frequencyType === 'cron'">
            <el-form-item label="Cron 表达式">
              <el-input v-model="form.frequency" placeholder="例如：0 */6 * * *" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20" v-if="form.mode === 'incremental'" style="margin-top: 8px;">
          <el-col :span="12">
            <el-form-item label="增量类型">
              <el-radio-group v-model="form.incremental.type">
                <el-radio label="id">自增ID</el-radio>
                <el-radio label="timestamp">时间戳字段</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="增量字段">
              <el-select v-model="form.incremental.field" filterable placeholder="选择或输入字段名" allow-create default-first-option>
                <el-option v-for="f in incrementalFieldOptions" :key="f" :label="f" :value="f" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
    </el-form>
  </div>
</template>

<script setup name="DataIntegrationTaskDetail">
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const incrementalFieldOptions = ref(['id', 'updated_at', 'create_time', 'ts'])

// 样例数据源（模拟“数据源管理”中已创建的数据源）
function ensureSampleDatasources() {
  const raw = localStorage.getItem('di_datasources')
  if (raw) return
  const datasources = [
    { id: 101, type: 'database', dbType: 'mysql', name: 'MySQL_A', host: '192.168.1.10', port: 3306, databases: ['sales', 'crm', 'logs'], tables: { sales: ['users','orders','order_items','products'], crm: ['customers','leads','activities'], logs: ['events','audit'] } },
    { id: 102, type: 'database', dbType: 'postgres', name: 'Postgres_B', host: '192.168.1.20', port: 5432, databases: ['analytics','dwh'], tables: { analytics: ['sessions','pageviews','orders'], dwh: ['facts','dim_users'] } },
    { id: 201, type: 'cluster', clusterType: 'hive', name: 'Hive_1', host: 'hive-server', port: 10000, databases: ['default','warehouse'], tables: { default: ['events','logs'], warehouse: ['ods_orders','ods_users'] } },
  ]
  localStorage.setItem('di_datasources', JSON.stringify(datasources))
}

const form = reactive({
  id: null,
  name: '',
  syncType: 'dbToDb',
  scope: 'single',
  sourceDsId: null,
  sourceDatabases: [],
  targetDsId: null,
  targetDatabase: '',
  range: { type: 'tables', tables: [], shardRule: '' },
  mode: 'incremental',
  incremental: { type: 'id', field: 'id' },
  frequencyType: 'manual',
  frequency: '',
  status: 'paused',
})

const sourceType = ref('database')
const targetType = ref('database')
const sourceOptions = ref([])
const targetOptions = ref([])
const sourceDbOptions = ref([])
const targetDbOptions = ref([])
const tableOptions = ref([])

function goList() { router.push('/dataintegration/tasks') }

function loadTask() {
  ensureSampleDatasources()
  const id = route.params.id
  const scope = route.query.scope
  const syncType = route.query.syncType
  if (id && id !== 'new') {
    try {
      const raw = localStorage.getItem('di_tasks')
      const arr = raw ? JSON.parse(raw) : []
      const found = arr.find(t => String(t.id) === String(id))
      if (found) {
        Object.assign(form, found)
        syncTypePreset(form.syncType)
        buildOptions()
      }
    } catch (e) {}
  } else {
    if (syncType) form.syncType = syncType
    if (scope) form.scope = scope
    form.name = presetName(form.syncType, form.scope)
    if (form.scope === 'full') { form.range.type = 'all'; form.range.tables = [] }
    syncTypePreset(form.syncType)
    buildOptions()
  }
}

function saveTask() {
  try {
    const raw = localStorage.getItem('di_tasks')
    const arr = raw ? JSON.parse(raw) : []
    if (!form.id) {
      form.id = (arr.length ? Math.max(...arr.map(t => t.id)) : 0) + 1
    }
    const brief = {
      id: form.id,
      name: form.name || '未命名任务',
      syncType: form.syncType,
      scope: form.scope,
      mode: form.mode,
      frequency: form.frequencyType === 'cron' ? (form.frequency || '未设置') : '手动',
      status: form.status,
      sourceBrief: sourceBrief(),
      targetBrief: targetBrief(),
    }
    const idx = arr.findIndex(t => t.id === form.id)
    if (idx >= 0) arr[idx] = brief; else arr.push(brief)
    localStorage.setItem('di_tasks', JSON.stringify(arr))
    ElMessage.success('已保存任务')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

function startTask() { form.status = 'running'; saveTask(); }
function pauseTask() { form.status = 'paused'; saveTask(); }

function syncTypePreset(t) {
  if (t === 'dbToDb') { sourceType.value = 'database'; targetType.value = 'database' }
  else if (t === 'dbToCluster') { sourceType.value = 'database'; targetType.value = 'cluster' }
  else if (t === 'clusterToDb') { sourceType.value = 'cluster'; targetType.value = 'database' }
}

function presetName(t, s) {
  const tLabel = t === 'dbToDb' ? '数据库→数据库' : t === 'dbToCluster' ? '数据库→集群' : '集群→数据库'
  const sLabel = s === 'single' ? '单表' : s === 'full' ? '整库' : '分库分表'
  return `新建${tLabel}${sLabel}同步任务`
}

function getAllDatasources() {
  try {
    return JSON.parse(localStorage.getItem('di_datasources') || '[]')
  } catch (e) { return [] }
}

function buildOptions() {
  const all = getAllDatasources()
  sourceOptions.value = all.filter(d => d.type === sourceType.value)
  targetOptions.value = all.filter(d => d.type === targetType.value)
  loadSourceDatabases()
  loadTargetDatabases()
}

function onSourceTypeChange() { buildOptions() }
function onTargetTypeChange() { buildOptions() }

function loadSourceDatabases() {
  const all = getAllDatasources()
  const ds = all.find(d => d.id === form.sourceDsId)
  sourceDbOptions.value = ds ? (ds.databases || []) : []
  // 合并所选库的表名（简单聚合）
  tableOptions.value = []
  if (ds && ds.tables && form.sourceDatabases && form.sourceDatabases.length) {
    const set = new Set()
    form.sourceDatabases.forEach(db => {
      (ds.tables[db] || []).forEach(t => set.add(t))
    })
    tableOptions.value = Array.from(set)
  }
}

function loadTargetDatabases() {
  const all = getAllDatasources()
  const ds = all.find(d => d.id === form.targetDsId)
  targetDbOptions.value = ds ? (ds.databases || []) : []
}

function sourceBrief() {
  const all = getAllDatasources()
  const ds = all.find(d => d.id === form.sourceDsId)
  const dsName = ds ? ds.name : '未选择'
  const dbs = form.sourceDatabases && form.sourceDatabases.length ? form.sourceDatabases.join(',') : '未选择库'
  return `${dsName}.${dbs}`
}

function targetBrief() {
  const all = getAllDatasources()
  const ds = all.find(d => d.id === form.targetDsId)
  const dsName = ds ? ds.name : '未选择'
  const db = form.targetDatabase || '未选择库'
  return `${dsName}.${db}`
}

onMounted(loadTask)
</script>

<style scoped>
.card-box :deep(.el-card__header) { font-weight: 600; }
</style>