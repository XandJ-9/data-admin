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
import { toRef, ref, onMounted, watch, computed } from 'vue'
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
    console.log('selector source', source)
}, {deep: true})


// function updateSourceData() {
    // source.value = {
    //     dataSourceId: Array.isArray(selectedDs.value) ? selectedDs.value : [selectedDs.value],
    //     database: Array.isArray(selectedDb.value) ? selectedDb.value : [selectedDb.value],
    //     table: Array.isArray(selectedTb.value) ? selectedTb.value : [selectedTb.value]
    // }
    // emit('update:source', source.value)
    // emit('update:columns', columns.value)

// }

// watch(() => source.dataSourceId, async (ids) => {
//     databaseList.value = []
//     tableList.value = []
//     if (props.datasourceMultiple) {
//         const reqs = ids.map(async dsId =>
//             await listDatabases({ dataSourceId: dsId }).then(res => ({ dsId, data: res?.data || [] }))
//         )
//         Promise.all(reqs).then(results => {
//             results.forEach(({ dsId, data }) => {
//                 const dsName = datasourceList.value.find(d => d.dataSourceId === dsId)?.dataSourceName || ''
//                 // databaseList.forEach(dbName => {})
//                 databaseList.value.push(...data.map(dbName => ({
//                     key: `${dsId}:${dbName}`,
//                     label: `${dsName}/${dbName}`,
//                     name: dbName,
//                     dataSourceId: dsId
//                 })))
//             })
//         })

//       if (!databaseList.value.length) {
//         const tabReqs = ids.map(async dsId =>
//             await listTables({dataSourceId: dsId}).then(res => ({dsId, data: res?.rows}))
//         )
//         Promise.all(tabReqs).then(result => {
//           result.forEach(({ dsId, data }) => {
//             const dsName = datasourceList.value.find(d => d.dataSourceId === dsId)?.dataSourceName || ''
//             tableList.value.push(...data.map(tb => ({
//                 key: `${dsId}:${tb.tableName}`,
//                 label: `${dsName}/${tb.tableName}`,
//                 name: tb.tableName,
//                 dataSourceId: dsId
//             })))
//           })
//         })
//         }
//     } else {
//         const dsId = ids
//         const dsName = datasourceList.value.find(d => d.dataSourceId === dsId)?.dataSourceName || ''
//         await listDatabases({ dataSourceId: ids }).then(res => {
//             const arr = res?.data || []
//             databaseList.value = arr.map(dbName => ({
//                 key: `${dsId}:${dbName}`,
//                 label: `${dsName}/${dbName}`,
//                 name: dbName,
//                 dataSourceId: dsId
//             }))
//         })

//       if(!databaseList.value.length){
//         await listTables({dataSourceId: dsId}).then(res => {
//           const arr = res?.rows || []
//           tableList.value = arr.map(tb => ({
//               key: `${dsId}:${tb.tableName}`,
//               label: `${tb.tableName}`,
//               name: tb.tableName,
//               databaseName: dsName,
//               dataSourceId: dsId
//           }))
//       })
//     }
//     }
//     console.log('datasourceList', datasourceList.value,
//         '\ndatabaseList', databaseList.value,
//         '\ntableList', tableList.value,
//         '\nsource', source.value)
//     updateSourceData()
// })

// watch(() => source.database, (val) => {
//     const databases = val
//     tableList.value = []
//     if (props.databaseMultiple) {
//         const reqs = databases.map(db =>
//             listTables({ dataSourceId: db.dataSourceId, databaseName: db.name }).then(res => ({ db, data: res?.rows || [] }))
//         )
//         Promise.all(reqs).then(results => {
//             results.forEach(({ db, data }) => {
//                 // databaseList.forEach(dbName => {})
//                 tableList.value.push(...data.map(tb => ({
//                     key: `${db.key}:${tb.tableName}`,
//                     label: `${tb.tableName}`,
//                     name: tb.tableName,
//                     databaseName: db.name,
//                     dataSourceId: db.dataSourceId
//                 })))
//             })
//         })
//     } else {
//         const dbName = databases.name || ''
//         listTables({ dataSourceId: databases.dataSourceId, databaseName: dbName }).then(res => {
//             const arr = res?.rows || []
//             tableList.value = arr.map(tb => ({
//                 key: `${databases.key}:${tb.tableName}`,
//                 label: `${tb.tableName}`,
//                 name: tb.tableName,
//                 databaseName: dbName,
//                 dataSourceId: databases.dataSourceId
//             }))
//         })
//     }
//     updateSourceData()
// })

// watch(() => source.table, async (val) => {
//     const tables = val
//     columns.value = []
//     let table = null;
//     if (props.tableMultiple) {
//         table = tables.first()
//     } else {
//         table = tables
//     }
//     if(!table) return
//     await listColumns({ dataSourceId: table.dataSourceId, databaseName: table.databaseName, tableName: table.name })
//         .then(res => {
//         const cols = res?.rows || []
//             columns.value = cols.map(c => c.name)
//         })
//     // console.log('watch table and columns', table, columns.value)
//     updateSourceData()
// })


const handleDataSourceChange = async () => {
    if (!source.dataSourceId) return
    databaseList.value = []
    tableList.value = []
    if (props.datasourceMultiple) { 
        const dsArr = source.dataSourceId
        dsArr.forEach(async dsId => {
            await listDatabases({ dataSourceId: dsId }).then(res => { 
                const arr = res?.data || []
                databaseList.value.push(...arr.map(dbName => ({
                    key: `${dsId}:${dbName}`,
                    label: `${dbName}`,
                    name: dbName,
                    dataSourceId: dsId
                })))
                console.log('handleDataSourceChange, database list => ', databaseList.value)
            })
            if(!databaseList.value.length){
                await listTables({dataSourceId: dsId}).then(res => { 
                    const arr = res?.rows || []
                    tableList.value = arr.map(tb => ({
                        key: `${dsId}:${tb.tableName}`,
                        label: `${tb.tableName}`,
                        name: tb.tableName,
                        databaseName: dsName,
                        dataSourceId: dsId
                    }))
                })
            }
        })
    }else{
        const dsId = source.dataSourceId
        await listDatabases({ dataSourceId: dsId }).then(res => { 
            const arr = res?.data || []
            databaseList.value = arr.map(dbName => ({
                key: `${dsId}:${dbName}`,
                label: `${dbName}`,
                name: dbName,
                dataSourceId: dsId
            }))
            console.log('handleDataSourceChange, database list => ', databaseList.value)
        })
        if(!databaseList.value.length){
            await listTables({dataSourceId: dsId}).then(res => { 
                const arr = res?.rows || []
                tableList.value = arr.map(tb => ({
                    key: `${dsId}:${tb.tableName}`,
                    label: `${tb.tableName}`,
                    name: tb.tableName,
                    databaseName: dsName,
                    dataSourceId: dsId
                }))
            })
        }
    }

}

const handleDatabaseChange = () => {

}

const handleTableChange = () => { 

}

onMounted(() => { 
    listDatasource().then(res => { 
        datasourceList.value = res.rows || []
    })
})
</script>
