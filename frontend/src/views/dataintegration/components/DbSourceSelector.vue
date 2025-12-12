<template>
    <div>
        <el-form :model="source" label-width="120px">
            <el-form-item label="数据源" label-position="top"> 
                <el-select v-model="source.dataSourceIds" :multiple="datasourceMultiple" filterable placeholder="请选择数据源">
                    <el-option v-for="item in datasourceList" :key="item.dataSourceId" :label="item.dataSourceName" :value="item.dataSourceId"/>
                </el-select>
            </el-form-item>
            <el-form-item v-if="databaseList.length" label="数据库" label-position="top"> 
                <!-- 当选项是数组对象时，需要指定对象中的key,这样才能定位到被选项，使用  value-key指定对象中的唯一值字段 -->
                <el-select v-model="source.databases" :multiple="databaseMultiple" filterable placeholder="请选择数据库" value-key="key">
                    <el-option v-for="item in databaseList" :key="item.key" :label="item.label" :value="item"/>
                </el-select>
            </el-form-item>
            <el-form-item label="数据表" label-position="top">
                <el-select v-model="source.tables" :multiple="tableMultiple" filterable placeholder="请选择数据表">
                    <el-option v-for="item in tableList" :key="item.key" :label="item.label" :value="item.key"/>
                </el-select>
            </el-form-item>
        </el-form>
        <el-button type="primary" @click="showInfo">显示父组件传递信息</el-button>
    </div>
</template>

<script setup>
import { toRefs, ref, onMounted, watch} from 'vue'
import { listDatasource, listDatabases, listTables } from '@/api/datasource'

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

// const emit = defineEmits(['update:source'])
// 监听数据变化，触发父组件更新
// watch(() => source.value.dataSourceIds, (ids) => {
//     source.value.dataSourceIds = ids
//     emit('update:source', source.value)
// })

const { source, columns } = toRefs(props)

const datasourceList = ref([])
const databaseList = ref([])
const tableList = ref([])


const loadDs = ()=>{
    listDatasource().then(res => {
        datasourceList.value = res.rows
    })
}

watch(() => source.value.dataSourceIds, (ids) => {
    databaseList.value = []
    tableList.value = []
    if (Array.isArray(ids)) {
        const reqs = ids.map(dsId =>
            listDatabases({ dataSourceId: dsId }).then(res => ({ dsId, data: res?.data || [] }))
        )
        Promise.all(reqs).then(results => {
            results.forEach(({ dsId, data }) => {
                let dsName = datasourceList.value.find(d => d.dataSourceId === dsId)?.dataSourceName || ''
                // databaseList.forEach(dbName => {})
                databaseList.value.push(...data.map(dbName => ({
                    key: `${dsId}:${dbName}`,
                    label: `${dsName}/${dbName}`,
                    name: dbName,
                    dataSourceId: dsId
                })))
            })
        })
    } else {
        const dsName = datasourceList.value.find(d => d.dataSourceId === ids)?.dataSourceName || ''
        listDatabases({ dataSourceId: ids }).then(res => {
            const arr = res?.data || []
            databaseList.value = arr.map(dbName => ({
                key: `${ids}:${dbName}`,
                label: `${dsName}/${dbName}`,
                name: dbName,
                dataSourceId: ids
            }))
        })
    }
})

watch(() => source.value.databases, (databases) => {
    tableList.value = []
    if (Array.isArray(databases)) {
        const reqs = databases.map(db =>
            listTables({ dataSourceId: db.dataSourceId, databaseName: db.name }).then(res => ({ db, data: res?.rows || [] }))
        )
        Promise.all(reqs).then(results => {
            results.forEach(({ db, data }) => {
                // databaseList.forEach(dbName => {})
                tableList.value.push(...data.map(tb => ({
                    key: `${db.key}:${tb.tableName}`,
                    label: `${db.label}/${tb.tableName}`,
                    name: tb.tableName,
                    databaseName: db.name,
                    dataSourceId: db.dataSourceId
                })))
            })
        })
        console.log('database multi', databases)
    } else {
        console.log('database sigle', databases)
    }
    
})

const showInfo = () => {
    console.log(source.value)
}

onMounted(()=>{
    loadDs()
})
</script>
