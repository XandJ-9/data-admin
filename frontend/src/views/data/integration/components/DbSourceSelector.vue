<template>
    <div>
        <el-form :model="source" label-width="120px">
            <el-form-item label="数据源" label-position="top"> 
                <el-select v-model="source.dataSourceId" :multiple="datasourceMultiple" filterable placeholder="请选择数据源"
                @change="handleDataSourceChange"
                >
                    <el-option v-for="item in datasourceList" :key="item.dataSourceId" :label="item.dataSourceName" :value="item.dataSourceId"/>
                </el-select>
            </el-form-item>
            <el-form-item v-if="databaseList.length" label="数据库" label-position="top"> 
                <!-- 当选项是数组对象时，需要指定对象中的key,这样才能定位到被选项，使用  value-key指定对象中的唯一值字段 -->
                <el-select v-model="source.database" :multiple="databaseMultiple" filterable placeholder="请选择数据库" value-key="key"
                @change="handleDatabaseChange"
                >
                    <el-option v-for="item in databaseList" :key="item.key" :label="item.label" :value="item"/>
                </el-select>
            </el-form-item>
            <el-form-item label="数据表" label-position="top">
                <el-select v-model="source.table" :multiple="tableMultiple" filterable placeholder="请选择数据表" value-key="key"
                @change="handleTableChange"
                >
                    <el-option v-for="item in tableList" :key="item.key" :label="item.label" :value="item"/>
                </el-select>
            </el-form-item>
        </el-form>
    </div>
</template>

<script setup>
import { ref, onMounted, watch, reactive, toRaw } from 'vue'
import { listDatasource, listDatabases, listTables, listColumns } from '@/api/data/asset'

const props = defineProps({
  source: {
    type: Object,
    default: () => ({})
  },
  columns: {
    type: Array,
    default: () => []
  },
  datasourceMultiple: {
    type: Boolean,
    default: false
  },
  databaseMultiple: {
    type: Boolean,
    default: false
  },
  tableMultiple: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:source', 'update:columns'])

const source = reactive({
  dataSourceId: props.source?.dataSourceId,
  database: props.source?.database,
  table: props.source?.table
})
const columns = ref(Array.isArray(props.columns) ? [...props.columns] : [])
const datasourceList = ref([])
const databaseList = ref([])
const tableList = ref([])

let lastSyncedSig = sig(props.source)
let lastEmittedSig = ''
let lastEmittedColsSig = ''

function emitUpdate() {
  const raw = toRaw(source)
  lastEmittedSig = sig(raw)
  lastEmittedColsSig = colsSig(columns.value)
  emit('update:source', {
    dataSourceId: raw.dataSourceId,
    database: raw.database,
    table: raw.table
  })
  emit('update:columns', [...columns.value])
}

function normalizeToArray(v) {
  if (!v) return []
  return Array.isArray(v) ? v : [v]
}

function sortUniq(arr) {
  return Array.from(new Set(arr)).sort()
}

function sig(val) {
  const ds = normalizeToArray(val?.dataSourceId).map((x) => String(x))
  const db = normalizeToArray(val?.database).map((x) => String(x?.key ?? x?.name ?? ''))
  const tb = normalizeToArray(val?.table).map((x) => String(x?.key ?? x?.name ?? ''))
  return `ds=${sortUniq(ds).join(',')};db=${sortUniq(db).join(',')};tb=${sortUniq(tb).join(',')}`
}

function colsSig(val) {
  if (!Array.isArray(val)) return ''
  return sortUniq(val.map((x) => String(x))).join(',')
}

const loadMetadata = async (preserve = false) => {
  if (!preserve) {
    source.database = props.databaseMultiple ? [] : undefined
    source.table = props.tableMultiple ? [] : undefined
  }
  databaseList.value = []
  if (!preserve) {
    tableList.value = []
    columns.value = []
  }

  if (!source.dataSourceId || (Array.isArray(source.dataSourceId) && source.dataSourceId.length === 0)) {
    return
  }

  const dsIds = Array.isArray(source.dataSourceId) ? source.dataSourceId : [source.dataSourceId]

  const getDsName = (id) => datasourceList.value.find(d => d.dataSourceId === id)?.dataSourceName || ''

  try {
    const dbPromises = dsIds.map(async (dsId) => {
      const res = await listDatabases({ dataSourceId: dsId })
      return { dsId, data: res.data || [] }
    })

    const dbResults = await Promise.all(dbPromises)

    dbResults.forEach(({ dsId, data }) => {
      if (data.length > 0) {
        const dsName = getDsName(dsId)
        databaseList.value.push(...data.map(dbName => ({
          key: `${dsId}:${dbName}`,
          label: props.datasourceMultiple ? `${dsName} > ${dbName}` : dbName,
          name: dbName,
          dataSourceId: dsId
        })))
      }
    })

    if (databaseList.value.length === 0) {
      const tablePromises = dsIds.map(async (dsId) => {
        const res = await listTables({ dataSourceId: dsId })
        return { dsId, data: res.rows || [] }
      })
      const tableResults = await Promise.all(tablePromises)

      tableList.value = []
      tableResults.forEach(({ dsId, data }) => {
        const dsName = getDsName(dsId)
        tableList.value.push(...data.map(tb => ({
          key: `${dsId}:${tb.tableName}`,
          label: props.datasourceMultiple ? `${dsName} > ${tb.tableName}` : tb.tableName,
          name: tb.tableName,
          dataSourceId: dsId
        })))
      })
    }
  } catch (e) {
    console.error('Failed to load metadata', e)
  }
}

const handleDataSourceChange = async () => {
  await loadMetadata(false)
  emitUpdate()
}

const loadTables = async (preserve = false) => {
  if (!preserve) {
    source.table = props.tableMultiple ? [] : undefined
  }
  tableList.value = []
  if (!preserve) {
    columns.value = []
  }

  const selectedDbs = Array.isArray(source.database) ? source.database : (source.database ? [source.database] : [])

  if (selectedDbs.length === 0) {
    if (databaseList.value.length > 0) {
      return
    }
  }

  if (databaseList.value.length === 0 && tableList.value.length > 0) {
    return
  }

  try {
    const tablePromises = selectedDbs.map(async (db) => {
      const res = await listTables({ dataSourceId: db.dataSourceId, databaseName: db.name })
      return { db, data: res.rows || [] }
    })

    const tableResults = await Promise.all(tablePromises)

    tableResults.forEach(({ db, data }) => {
      tableList.value.push(...data.map(tb => ({
        key: `${db.key}:${tb.tableName}`,
        label: props.databaseMultiple || props.datasourceMultiple ? `${db.label} > ${tb.tableName}` : tb.tableName,
        name: tb.tableName,
        dataSourceId: db.dataSourceId,
        databaseName: db.name
      })))
    })
  } catch (e) {
    console.error('Failed to load tables', e)
  }
}

const handleDatabaseChange = async () => {
  await loadTables(false)
  emitUpdate()
}

const loadColumns = async (preserve = false) => {
  if (!preserve) {
    columns.value = []
  }
  const selectedTables = Array.isArray(source.table) ? source.table : (source.table ? [source.table] : [])

  if (selectedTables.length === 0) {
    return
  }

  try {
    const colPromises = selectedTables.map(async (t) => {
      const res = await listColumns({
        dataSourceId: t.dataSourceId,
        databaseName: t.databaseName,
        tableName: t.name
      })
      const rows = res.rows || []
      return rows.map(c => c.name).filter(Boolean)
    })

    const colsList = await Promise.all(colPromises)
    const merged = []
    const seen = new Set()
    colsList.flat().forEach((c) => {
      if (seen.has(c)) return
      seen.add(c)
      merged.push(c)
    })
    columns.value = merged
  } catch (e) {
    console.error('Failed to load columns', e)
  }
}

const handleTableChange = async () => { 
  await loadColumns(false)
  emitUpdate()
}

const initData = async () => {
  if (!source.dataSourceId) return
  await loadMetadata(true)
  if (databaseList.value.length > 0) {
    if (source.database) {
      await loadTables(true)
      if (source.table) await loadColumns(true)
    }
    emitUpdate()
    return
  }
  if (source.table) await loadColumns(true)
  emitUpdate()
}

onMounted(() => { 
  listDatasource().then(res => {
    datasourceList.value = res.rows || []
    initData()
  })
})

watch(
  () => [props.source, props.columns],
  async ([src, cols]) => {
    const nextSig = sig(src)
    const nextColsSig = colsSig(cols)
    if (nextSig === lastEmittedSig && nextColsSig === lastEmittedColsSig) return
    if (nextSig !== lastSyncedSig) {
      source.dataSourceId = src?.dataSourceId
      source.database = src?.database
      source.table = src?.table
      lastSyncedSig = nextSig
    }
    if (Array.isArray(cols)) columns.value = [...cols]
    if (datasourceList.value.length > 0 && source.dataSourceId) {
      await initData()
    }
  },
  { deep: true, immediate: true }
)
</script>
