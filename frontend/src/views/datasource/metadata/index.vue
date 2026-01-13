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
                <el-button type="primary" :disabled="!dsId || asyncCollecting" @click="handleCollectAsync">
                    整库源数据采集
                </el-button>
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

        <!-- 进度对话框 -->
        <el-dialog v-model="collectProgressVisible" title="采集进度" width="500px" :close-on-click-modal="false">
            <el-progress :percentage="collectProgress" :status="asyncCollecting ? '' : 'success'" />
            <p style="margin-top: 16px; text-align: center;">{{ collectStatusText }}</p>
            <template #footer v-if="asyncCollecting">
                <el-button @click="handleCancelCollect">取消任务</el-button>
            </template>
        </el-dialog>

        <el-dialog v-model="columnsDialogVisible" title="字段信息" style="margin-top: 16px" modal-penetrable>
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
import { listTables, listColumns, collectMetaTable, listDatabases,
         collectMetaAsync, getCollectStatus, cancelCollect } from '@/api/datasource'
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
const columnsDialogVisible = ref(false)
const loading = ref(false)
const collecting = ref(false)

// 异步采集相关状态
const asyncCollecting = ref(false)
const currentTaskId = ref('')
const collectProgress = ref(0)
const collectStatusText = ref('')
const collectProgressVisible = ref(false)
const statusPollTimer = ref(null)

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
        columnsDialogVisible.value = true
    })
}

// 异步采集函数
async function handleCollectAsync() {
    if (!dsId.value) return
    asyncCollecting.value = true
    collectProgressVisible.value = true
    collectProgress.value = 0
    collectStatusText.value = '正在启动采集任务...'

    const payload = { dataSourceId: dsId.value }
    if (databaseName.value) payload.databaseName = databaseName.value

    try {
        const res = await collectMetaAsync(payload)
        currentTaskId.value = res.data.taskId
        collectStatusText.value = '任务已启动，正在采集...'
        startStatusPolling()
    } catch (error) {
        proxy.$modal.msgError(error.message || '启动采集任务失败')
        asyncCollecting.value = false
        collectProgressVisible.value = false
    }
}

function startStatusPolling() {
    if (statusPollTimer.value) {
        clearInterval(statusPollTimer.value)
    }

    statusPollTimer.value = setInterval(async () => {
        try {
            const res = await getCollectStatus(currentTaskId.value)
            const data = res.data
            collectProgress.value = data.progress || 0
            collectStatusText.value = `正在采集: ${data.currentTable || ''} (${data.collectedTables}/${data.totalTables})`

            if (['completed', 'failed', 'cancelled'].includes(data.status)) {
                clearInterval(statusPollTimer.value)
                statusPollTimer.value = null
                asyncCollecting.value = false

                if (status.status === 'completed') {
                    proxy.$modal.msgSuccess('采集完成')
                    collectStatusText.value = '采集完成'
                    getTables()
                } else if (data.status === 'failed') {
                    proxy.$modal.msgError(`采集失败: ${data.errorMessage || '未知错误'}`)
                } else {
                    collectStatusText.value = '已取消'
                }

                setTimeout(() => {
                    collectProgressVisible.value = false
                }, 2000)
            }
        } catch (error) {
            clearInterval(statusPollTimer.value)
            statusPollTimer.value = null
            asyncCollecting.value = false
            collectProgressVisible.value = false
        }
    }, 1000)
}

async function handleCancelCollect() {
    if (!currentTaskId.value) return
    try {
        await cancelCollect(currentTaskId.value)
        if (statusPollTimer.value) {
            clearInterval(statusPollTimer.value)
            statusPollTimer.value = null
        }
        asyncCollecting.value = false
        collectProgressVisible.value = false
        proxy.$modal.msgSuccess('任务已取消')
    } catch (error) {
        proxy.$modal.msgError(error.message || '取消任务失败')
    }
}

function handleCollectTable(t) {
    if (!dsId.value) return
    collecting.value = true
    const payload = { dataSourceId: dsId.value, databaseName: databaseName.value, tableName: t }
    collectMetaTable(payload).then(() => {
        proxy.$modal.msgSuccess('采集完成')
    }).finally(() => (collecting.value = false))
}

// 组件卸载时清理定时器
onUnmounted(() => {
    if (statusPollTimer.value) {
        clearInterval(statusPollTimer.value)
    }
})

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
