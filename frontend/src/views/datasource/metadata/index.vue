<template>
    <div class="app-container">
        <el-form :inline="true" style="margin-bottom: 12px">
            <el-form-item label="数据源">
                <el-select v-model="dsId" placeholder="选择数据源" style="width: 260px">
                    <el-option v-for="ds in dsList" :key="ds.dataSourceId"
                        :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
                </el-select>
            </el-form-item>
            <el-form-item v-if="dbList.length" label="数据库">
                <el-select filterable v-model="databaseName" placeholder="选择数据库" style="width: 240px" clearable>
                    <el-option v-for="db in dbList" :key="db" :label="db" :value="db" />
                </el-select>
            </el-form-item>
            <el-form-item>
                <el-button type="success" :disabled="!dsId" @click="getTables">加载业务表</el-button>
                <el-button type="primary" :disabled="!dsId || collecting" @click="handleCollect">采集元数据</el-button>
            </el-form-item>
        </el-form>
        <el-form-item label="筛选">
            <el-input v-model="filterName" placeholder="搜索表名" />
        </el-form-item>
        <el-table v-loading="loading" :data="displayTables" row-key="tableName" style="width: 100%; margin-top: 20px"
            height="60vh" border>
            <el-table-column prop="tableName" label="表名" />
            <el-table-column prop="comment" label="表注释" />
            <el-table-column prop="databaseName" label="数据库名" />
            <el-table-column prop="createTime" label="创建时间" />
            <el-table-column prop="updateTime" label="更新时间" />
            <el-table-column label="操作" width="220">
                <template #default="scope">
                    <el-button size="small" @click="loadColumns(scope.row.tableName)">查看字段</el-button>
                    <el-button type="warning" size="small"
                        @click="handleCollectTable(scope.row.tableName)">采集</el-button>
                </template>
            </el-table-column>
        </el-table>

        <el-dialog v-if="columns.length" v-model="columns.length" title="字段信息" style="margin-top: 16px">
            <h4>表名：{{ currentTable }}</h4>
            <el-table :data="columns" style="width: 100%; margin-top: 20px" height="60vh" border>
                <el-table-column prop="order" label="序号" width="80" />
                <el-table-column prop="name" label="列名" />
                <el-table-column prop="comment" label="列注释" />
                <el-table-column prop="type" label="类型" />
                <el-table-column prop="notnull" label="非空" width="80">
                    <template #default="scope"><el-tag
                            :type="scope.row.notnull ? 'danger' : 'info'">{{ scope.row.notnull ? '是' : '否' }}</el-tag></template>
                </el-table-column>
                <el-table-column prop="primary" label="主键" width="80">
                    <template #default="scope"><el-tag
                            :type="scope.row.primary ? 'success' : 'info'">{{ scope.row.primary ? '是' : '否' }}</el-tag></template>
                </el-table-column>
                <el-table-column prop="default" label="默认值" />
            </el-table>
        </el-dialog>
    </div>
</template>

<script setup name="DataSourceMetadata">
import { listDatasource } from '@/api/datasource'
import { listTables, listColumns, collectMeta, collectMetaTable, listDatabases } from '@/api/datasource'
const { proxy } = getCurrentInstance()

const dsId = ref()
const dsList = ref([])
const dbList = ref([])
const databaseName = ref('')
const tables = ref([])
const filterName = ref('')
const displayTables = computed(() => {
    const kw = (filterName.value || '').trim().toLowerCase()
    if (!kw) return tables.value
    return tables.value.filter(t => String(t.tableName || '').toLowerCase().includes(kw))
})
const columns = ref([])
const currentTable = ref('')
const loading = ref(false)
const collecting = ref(false)

function getDsList() {
    listDatasource().then(res => {
        dsList.value = res.rows || []
    })
}

function getTables() {
    if (!dsId.value) return
    loading.value = true
    const params = { dataSourceId: dsId.value }
    if (databaseName.value) params.databaseName = databaseName.value
    listTables(params).then(res => {
        tables.value = res.rows || []
    }).finally(() => (loading.value = false))
}

function loadColumns(t) {
    if (!dsId.value) return
    currentTable.value = t
    const params = { dataSourceId: dsId.value, tableName: t }
    if (databaseName.value) params.databaseName = databaseName.value
    listColumns(params).then(res => {
        columns.value = res.rows || []
    })
}

function handleCollect() {
    if (!dsId.value) return
    collecting.value = true
    const payload = { dataSourceId: dsId.value }
    if (databaseName.value) payload.databaseName = databaseName.value
    collectMeta(payload).then(() => {
        proxy.$modal.msgSuccess('采集完成')
        getTables()
    }).finally(() => (collecting.value = false))
}

function handleCollectTable(t) {
    if (!dsId.value) return
    collecting.value = true
    const payload = { dataSourceId: dsId.value, databaseName: databaseName.value, tableName: t }
    collectMetaTable(payload).then(() => {
        proxy.$modal.msgSuccess('采集完成')
        // loadColumns(t)
    }).finally(() => (collecting.value = false))
}

onMounted(() => {
    getDsList()
})

watch(dsId, v => {
    dbList.value = []
    databaseName.value = ''
    if (!v) return
    listDatabases({ dataSourceId: v }).then(res => {
        const dbs = res.data
        if (Array.isArray(dbs)) dbList.value = dbs
    })
})
</script>

<style scoped></style>
