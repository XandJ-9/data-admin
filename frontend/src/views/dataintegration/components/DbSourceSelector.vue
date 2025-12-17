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
import { ref, onMounted, watch, reactive } from 'vue'
import { listDatasource, listDatabases, listTables, listColumns } from '@/api/datasource'

const props = defineProps({
  source: {
    type: Object,
    default: () => ({})
    },
  columns: {
    type: Array,
    default: () => []
    },
    datasourceMultiple: false,
    databaseMultiple: false,
    tableMultiple: false
})

const emit = defineEmits(['update:source', 'update:columns'])

const source = reactive({
    dataSourceId: undefined,
    database: undefined,
    table: undefined
})
const columns = ref([])
const datasourceList = ref([])
const databaseList = ref([])
const tableList = ref([])


watch(() => props.source, (val) => {
    if(source.dataSourceId !== val.dataSourceId) {
        source.dataSourceId = val.dataSourceId
    }
    if(source.database !== val.database) {
        source.database = val.database
    }
    if(source.table !== val.table) {
        source.table = val.table
    }
    // console.log('selector source', source)
}, {deep: true})

function emitUpdate() {
    emit('update:source', source)
    emit('update:columns', columns.value)
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
        emitUpdate()
        return
    }

    const dsIds = Array.isArray(source.dataSourceId) ? source.dataSourceId : [source.dataSourceId]
    
    const getDsName = (id) => datasourceList.value.find(d => d.dataSourceId === id)?.dataSourceName || ''

    try {
        // Fetch databases for all selected sources
        const dbPromises = dsIds.map(async (dsId) => {
            const res = await listDatabases({ dataSourceId: dsId })
            return { dsId, data: res.data || [] }
        })

        const dbResults = await Promise.all(dbPromises)
        
        let hasDatabases = false
        dbResults.forEach(({ dsId, data }) => {
            if (data.length > 0) {
                hasDatabases = true
                const dsName = getDsName(dsId)
                databaseList.value.push(...data.map(dbName => ({
                    key: `${dsId}:${dbName}`,
                    label: props.datasourceMultiple ? `${dsName} > ${dbName}` : dbName,
                    name: dbName,
                    dataSourceId: dsId
                })))
            }
        })

        // If no databases found, try fetching tables directly
        if (databaseList.value.length === 0) {
            const tablePromises = dsIds.map(async (dsId) => {
                 const res = await listTables({ dataSourceId: dsId })
                 return { dsId, data: res.rows || [] }
            })
            const tableResults = await Promise.all(tablePromises)
            
            // Only clear table list if we are repopulating it here
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
    
    emitUpdate()
}

const handleDataSourceChange = async () => {
    await loadMetadata(false)
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
        // If no DB selected, and we are not in "no-db" mode (which is handled in loadMetadata), return
        // But wait, if databaseList is empty, we might be in "no-db" mode. 
        // If databaseList is NOT empty, and no DB selected, then tableList should be empty.
        if (databaseList.value.length > 0) {
            emitUpdate()
            return
        }
        // If databaseList is empty, loadMetadata might have already populated tableList.
        // So we shouldn't clear it here if we came from loadMetadata?
        // Actually handleDatabaseChange is only called when database selection changes.
        // So if databaseList is empty, this function is unlikely to be called by user.
        // But for initialization, we need to be careful.
    }

    if (databaseList.value.length === 0 && tableList.value.length > 0) {
        // "No-database" mode (e.g. flat datasource), tables already loaded by loadMetadata
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
    
    emitUpdate()
}

const handleDatabaseChange = async () => {
    await loadTables(false)
}

const loadColumns = async (preserve = false) => {
    if (!preserve) {
        columns.value = []
    }
    const selectedTables = Array.isArray(source.table) ? source.table : (source.table ? [source.table] : [])
    
    if (selectedTables.length === 0) {
        emitUpdate()
        return
    }
    
    try {
        // Fetch columns for the first selected table
        const firstTable = selectedTables[0]
        const res = await listColumns({ 
             dataSourceId: firstTable.dataSourceId, 
             databaseName: firstTable.databaseName, 
             tableName: firstTable.name 
        })
        
        if (res.rows) {
            columns.value = res.rows.map(c => c.name)
        }
    } catch (e) {
        console.error('Failed to load columns', e)
    }

    emitUpdate()
}

const handleTableChange = async () => { 
    await loadColumns(false)
}

const initData = async () => {
    if (source.dataSourceId) {
        await loadMetadata(true)
        if (source.database) {
            await loadTables(true)
            if (source.table) {
                await loadColumns(true)
            }
        }
    }
}

onMounted(() => { 
    listDatasource().then(res => { 
        datasourceList.value = res.rows || []
        // Initialize if props already provided
        initData()
    })
})

watch(() => props.source, async (val) => {
    const dsChanged = source.dataSourceId !== val.dataSourceId
    const dbChanged = source.database !== val.database
    const tbChanged = source.table !== val.table

    if(dsChanged) {
        source.dataSourceId = val.dataSourceId
    }
    if(dbChanged) {
        source.database = val.database
    }
    if(tbChanged) {
        source.table = val.table
    }
    
    // If external source changed (e.g. loaded from API), we might need to re-init lists
    // Only if lists are empty or mismatch?
    // Simple logic: if datasource changed, reload metadata. 
    // If datasource is same but we have no lists (page refresh?), reload.
    if (dsChanged || (val.dataSourceId && datasourceList.value.length > 0 && databaseList.value.length === 0 && tableList.value.length === 0)) {
         // Wait for next tick to ensure local source is updated? 
         // No, we just updated it above.
         // But we should be careful not to trigger double loads if user is interacting.
         // This watch is deep on props.source.
         // If user interacts, emitUpdate updates parent, parent updates prop, this watch triggers.
         // We need to avoid re-fetching if we initiated the change.
         // But here we are just syncing props to local.
         
         // If the change came from parent (and is not just an echo of our emit), we should reload.
         // But detecting "echo" is hard.
         // However, initData(true) preserves selection. Re-fetching lists with same ID shouldn't hurt much, just network calls.
         // To avoid excessive calls, we could check if lists are already populated for this ID.
         // For now, let's just call initData() if it looks like a new assignment.
         
         // Actually, if dsChanged is true, it means ID changed, so we MUST reload.
         if (dsChanged) {
             await loadMetadata(false) // New DS, reset downstream
         } else if (val.dataSourceId && databaseList.value.length === 0 && tableList.value.length === 0) {
             // Same DS, but no lists loaded yet (initial load scenario)
             await initData()
         }
    }
    
}, {deep: true})
</script>
