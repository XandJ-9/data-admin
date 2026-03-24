<template>
  <div class="app-container">
    <!-- 数据源基本信息 -->
    <el-card class="box-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">{{ dataSourceInfo.dataSourceName }}</span>
          <el-button type="primary" icon="Back" @click="goBack">返回数据源列表</el-button>
        </div>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="数据源名称">{{ dataSourceInfo.dataSourceName }}</el-descriptions-item>
        <el-descriptions-item label="数据库类型">
          <el-tag :type="getDbTypeTag(dataSourceInfo.dbType)">{{ dataSourceInfo.dbType }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="dataSourceInfo.status === '0' ? 'success' : 'danger'">
            {{ dataSourceInfo.status === '0' ? '正常' : '停用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="主机">{{ dataSourceInfo.host || '-' }}</el-descriptions-item>
        <el-descriptions-item label="端口">{{ dataSourceInfo.port || '-' }}</el-descriptions-item>
        <el-descriptions-item label="数据库">{{ dataSourceInfo.dbName }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ dataSourceInfo.username || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ dataSourceInfo.createTime }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">
          <div class="prewrap">{{ dataSourceInfo.remark || '-' }}</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 数据库列表 -->
    <el-card class="box-card mt-20" shadow="never" v-loading="databaseLoading" v-show="!selectedDatabase">
      <template #header>
        <div class="card-header">
          <span class="card-title">数据库列表</span>
          <div class="card-actions">
            <el-input
              v-model="databaseSearchText"
              placeholder="搜索数据库名"
              clearable
              style="width: 200px; margin-right: 10px"
              prefix-icon="Search"
            />
            <el-button type="primary" icon="Refresh" @click="loadDatabases" :loading="databaseLoading">刷新</el-button>
          </div>
        </div>
      </template>
      <el-table
        :data="filteredDatabaseList"
        border
        style="width: 100%"
        max-height="400"
        :empty-text="filteredDatabaseList.length === 0 ? (databaseSearchText ? '未找到匹配的数据库' : '暂无数据') : '点击加载按钮获取数据库列表'"
      >
        <el-table-column prop="databaseName" label="数据库名" min-width="200" />
        <el-table-column label="采集进度" min-width="250">
          <template #default="scope">
            <div v-if="scope.row.collecting && scope.row.progress">
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-progress
                  :percentage="scope.row.progress.total > 0 ? Math.round((scope.row.progress.current / scope.row.progress.total) * 100) : 0"
                  :status="scope.row.progress.status === 'failed' ? 'exception' : (scope.row.progress.status === 'completed' ? 'success' : '')"
                  style="flex: 1"
                />
                <el-tag v-if="scope.row.taskId" size="small" type="info" @close="cancelCollectionTask(scope.row)" closable>取消</el-tag>
              </div>
              <div style="font-size: 12px; color: #909399; margin-top: 4px;">
                {{ scope.row.progress.status }} - {{ scope.row.progress.current }}/{{ scope.row.progress.total }} 张表
              </div>
              <div v-if="scope.row.progress.error" style="font-size: 12px; color: #f56c6c; margin-top: 4px;">
                错误：{{ scope.row.progress.error }}
              </div>
            </div>
            <div v-else-if="scope.row.progress && scope.row.progress.status === 'completed'">
              <el-tag type="success" size="small">已完成 - {{ scope.row.progress.current }} 张表</el-tag>
            </div>
            <div v-else-if="scope.row.progress && scope.row.progress.status === 'failed'">
              <el-tag type="danger" size="small">失败 - {{ scope.row.progress.error || '未知错误' }}</el-tag>
            </div>
            <div v-else>
              <span style="color: #c0c4cc;">未开始</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="scope">
            <el-button size="small" icon="View" @click="viewTables(scope.row)">查看表</el-button>
            <el-button
              size="small"
              icon="Collection"
              type="primary"
              @click="collectDatabase(scope.row)"
              :loading="scope.row.collecting"
              :disabled="scope.row.collecting"
            >
              {{ scope.row.collecting ? '采集中...' : '采集' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 数据表列表 -->
    <el-card class="box-card mt-20" shadow="never" v-if="selectedDatabase" v-loading="tableLoading">
      <template #header>
        <div class="card-header">
          <div class="card-title-with-action">
            <el-tag type="primary" size="large" class="database-tag">当前数据库: {{ selectedDatabase }}</el-tag>
            <el-button type="info" icon="Back" @click="backToDatabases" link>返回数据库列表</el-button>
          </div>
          <div class="card-actions">
            <el-input
              v-model="tableSearchText"
              placeholder="搜索表名"
              clearable
              style="width: 200px; margin-right: 10px"
              prefix-icon="Search"
            />
            <el-button type="primary" icon="Refresh" @click="loadTables" :loading="tableLoading">刷新</el-button>
          </div>
        </div>
      </template>
      <el-table
        :data="filteredTableList"
        border
        style="width: 100%"
        max-height="400"
        :empty-text="filteredTableList.length === 0 ? (tableSearchText ? '未找到匹配的数据表' : '暂无数据') : ''"
      >
        <el-table-column prop="tableName" label="表名" min-width="200" />
        <el-table-column prop="tableType" label="表类型" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.tableType === 'BASE TABLE' ? 'primary' : 'info'" size="small">
              {{ scope.row.tableType || 'TABLE' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tableComment" label="表描述" min-width="200">
          <template #default="scope">
            <div class="prewrap">{{ scope.row.tableComment || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="scope">
            <el-button size="small" icon="View" @click="viewColumns(scope.row)">查看字段</el-button>
            <el-button size="small" icon="Collection" type="primary" @click="collectTable(scope.row)" :loading="scope.row.collecting">采集</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 字段详情对话框 -->
    <el-dialog
      :title="`字段详情 - ${selectedTable}`"
      v-model="columnDialogVisible"
      width="80%"
      append-to-body
    >
      <div v-loading="columnLoading">
        <el-input
          v-model="columnSearchText"
          placeholder="搜索字段名或描述"
          clearable
          style="margin-bottom: 16px"
          prefix-icon="Search"
        />
        <el-table
          :data="filteredColumnList"
          border
          style="width: 100%"
          :empty-text="filteredColumnList.length === 0 ? (columnSearchText ? '未找到匹配的字段' : '暂无数据') : ''"
        >
          <el-table-column prop="columnOrdinalPosition" label="序号" width="80" align="center" />
          <el-table-column prop="columnName" label="字段名" min-width="150" />
          <el-table-column prop="dataType" label="数据类型" width="120" />
          <el-table-column prop="columnType" label="完整类型" width="150" />
          <el-table-column prop="columnComment" label="字段描述" min-width="200">
            <template #default="scope">
              <div class="prewrap">{{ scope.row.columnComment || '-' }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="columnKey" label="键类型" width="100" align="center">
            <template #default="scope">
              <el-tag v-if="scope.row.columnKey === 'PRI'" type="success" size="small">主键</el-tag>
              <el-tag v-else-if="scope.row.columnKey === 'UNI'" type="warning" size="small">唯一</el-tag>
              <el-tag v-else-if="scope.row.columnKey === 'MUL'" type="info" size="small">索引</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="isNullable" label="可空" width="80" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.isNullable === 'YES' ? 'info' : 'warning'" size="small">
                {{ scope.row.isNullable === 'YES' ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="columnDefault" label="默认值" width="120" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup name="DataSourceDetail">
import { useRoute, useRouter } from 'vue-router'
import { getDatasource } from '@/api/data/datasource'
import { listDatabases, listTables, listColumns, collectMetaAsync, getCollectStatus, cancelCollect, collectMetaTable } from '@/api/data/asset'

const route = useRoute()
const router = useRouter()
const { proxy } = getCurrentInstance()

const dataSourceId = ref(route.params.id)
const dataSourceInfo = ref({})
const databaseList = ref([])
const tableList = ref([])
const columnList = ref([])
const selectedDatabase = ref('')
const selectedTable = ref('')

const databaseLoading = ref(false)
const tableLoading = ref(false)
const columnLoading = ref(false)
const columnDialogVisible = ref(false)

// 轮询定时器管理
const pollTimers = ref({})

// 搜索关键词
const databaseSearchText = ref('')
const tableSearchText = ref('')
const columnSearchText = ref('')

// 过滤后的数据库列表
const filteredDatabaseList = computed(() => {
  if (!databaseSearchText.value) {
    return databaseList.value
  }
  const searchText = databaseSearchText.value.toLowerCase().trim()
  return databaseList.value.filter(db =>
    db.databaseName && db.databaseName.toLowerCase().includes(searchText)
  )
})

// 过滤后的数据表列表
const filteredTableList = computed(() => {
  if (!tableSearchText.value) {
    return tableList.value
  }
  const searchText = tableSearchText.value.toLowerCase().trim()
  return tableList.value.filter(table =>
    (table.tableName && table.tableName.toLowerCase().includes(searchText)) ||
    (table.tableComment && table.tableComment.toLowerCase().includes(searchText))
  )
})

// 过滤后的字段列表
const filteredColumnList = computed(() => {
  if (!columnSearchText.value) {
    return columnList.value
  }
  const searchText = columnSearchText.value.toLowerCase().trim()
  return columnList.value.filter(col =>
    (col.columnName && col.columnName.toLowerCase().includes(searchText)) ||
    (col.columnComment && col.columnComment.toLowerCase().includes(searchText))
  )
})

// 加载数据源信息
function loadDataSourceInfo() {
  getDatasource(dataSourceId.value).then(response => {
    dataSourceInfo.value = response.data
  }).catch(() => {
    proxy.$modal.msgError('加载数据源信息失败')
  })
}

// 加载数据库列表
function loadDatabases() {
  if (!dataSourceInfo.value.dbType) {
    proxy.$modal.msgWarning('请先加载数据源信息')
    return
  }

  databaseLoading.value = true
  listDatabases({
    dataSourceId: dataSourceId.value,
    databaseName: ''
  }).then(response => {
    // 后端返回的是字符串数组，需要转换成对象数组
    const dbs = response.data || []
    databaseList.value = dbs.map(name => ({ databaseName: name }))
    if (databaseList.value.length === 0) {
      proxy.$modal.msgWarning('该数据源下没有数据库')
    }
  }).catch(() => {
    proxy.$modal.msgError('加载数据库列表失败')
  }).finally(() => {
    databaseLoading.value = false
  })
}

// 查看表列表
function viewTables(row) {
  selectedDatabase.value = row.databaseName
  selectedTable.value = ''
  tableList.value = []
  loadTables()
}

// 加载表列表
function loadTables() {
  if (!selectedDatabase.value) {
    proxy.$modal.msgWarning('请先选择数据库')
    return
  }

  tableLoading.value = true
  listTables({
    dataSourceId: dataSourceId.value,
    databaseName: selectedDatabase.value
  }).then(response => {
    // 后端返回的是 {rows: [...], total: ...}
    tableList.value = response.rows || []
    if (tableList.value.length === 0) {
      proxy.$modal.msgWarning(`数据库 ${selectedDatabase.value} 下没有数据表`)
    }
  }).catch(() => {
    proxy.$modal.msgError('加载表列表失败')
  }).finally(() => {
    tableLoading.value = false
  })
}

// 查看字段列表
function viewColumns(row) {
  selectedTable.value = row.tableName
  columnDialogVisible.value = true
  columnLoading.value = true

  listColumns({
    dataSourceId: dataSourceId.value,
    databaseName: selectedDatabase.value,
    tableName: selectedTable.value
  }).then(response => {
    // 后端返回的是 {rows: [...], total: ...}
    const rows = response.rows || []
    // 字段名映射
    columnList.value = rows.map(col => ({
      columnOrdinalPosition: col.order,
      columnName: col.name,
      dataType: col.type,
      columnType: col.type,
      columnComment: col.comment,
      columnKey: col.primary ? 'PRI' : '',
      isNullable: col.notnull ? 'NO' : 'YES',
      columnDefault: col.default
    }))
    if (columnList.value.length === 0) {
      proxy.$modal.msgWarning(`表 ${selectedTable.value} 没有字段信息`)
    }
  }).catch(() => {
    proxy.$modal.msgError('加载字段列表失败')
  }).finally(() => {
    columnLoading.value = false
  })
}

// 采集数据库（整库采集 - 异步）
function collectDatabase(row) {
  proxy.$modal.confirm(`是否确认采集数据库 "${row.databaseName}" 的元数据？`).then(() => {
    // 设置加载状态
    const dbItem = databaseList.value.find(db => db.databaseName === row.databaseName)
    if (dbItem) {
      dbItem.collecting = true
      dbItem.taskId = null
      dbItem.progress = { current: 0, total: 0, status: '启动中...' }
    }

    // 启动异步采集任务
    collectMetaAsync({
      dataSourceId: dataSourceId.value,
      databaseName: row.databaseName
    }).then(response => {
      const taskId = response.data.taskId
      if (dbItem) {
        dbItem.taskId = taskId
      }
      proxy.$modal.msgSuccess('采集任务已启动')

      // 开始轮询任务状态
      pollTaskStatus(taskId, row.databaseName)
    }).catch(() => {
      proxy.$modal.msgError('启动采集任务失败')
      if (dbItem) {
        dbItem.collecting = false
      }
    })
  }).catch(() => {})
}

// 轮询任务状态
function pollTaskStatus(taskId, databaseName) {
  // 清除可能存在的旧定时器
  if (pollTimers.value[databaseName]) {
    clearInterval(pollTimers.value[databaseName])
  }

  // 创建新的定时器
  pollTimers.value[databaseName] = setInterval(() => {
    getCollectStatus(taskId).then(response => {
      // response 是 {code: 200, msg: "操作成功", data: {...}}
      const status = response.data

      // 调试日志
      console.log('任务状态更新:', status)

      const dbIndex = databaseList.value.findIndex(db => db.databaseName === databaseName)

      if (dbIndex !== -1 && status) {
        // 使用后端返回的正确字段名（驼峰命名）
        databaseList.value[dbIndex].progress = {
          current: status.collectedTables || 0,
          total: status.totalTables || 0,
          status: status.status === 'running' ? '运行中' :
                   (status.status === 'completed' ? '已完成' :
                   (status.status === 'failed' ? '失败' :
                   (status.status === 'cancelled' ? '已取消' : status.status))),
          error: status.errorMessage || null
        }
      }

      // 任务完成或失败时停止轮询
      if (status && (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled')) {
        clearInterval(pollTimers.value[databaseName])
        delete pollTimers.value[databaseName]

        if (dbIndex !== -1) {
          databaseList.value[dbIndex].collecting = false
        }

        if (status.status === 'completed') {
          proxy.$modal.msgSuccess(`采集完成！成功采集 ${status.collectedTables} 张表`)
        } else if (status.status === 'failed') {
          proxy.$modal.msgError(`采集失败：${status.errorMessage || '未知错误'}`)
        } else if (status.status === 'cancelled') {
          proxy.$modal.msgWarning('采集任务已取消')
        }
      }
    }).catch(error => {
      console.error('查询任务状态失败:', error)
      clearInterval(pollTimers.value[databaseName])
      delete pollTimers.value[databaseName]

      const dbIndex = databaseList.value.findIndex(db => db.databaseName === databaseName)
      if (dbIndex !== -1) {
        databaseList.value[dbIndex].collecting = false
      }
      proxy.$modal.msgError('查询任务状态失败')
    })
  }, 2000) // 每2秒轮询一次
}

// 取消采集任务
function cancelCollectionTask(row) {
  if (!row.taskId) {
    proxy.$modal.msgWarning('没有可取消的任务')
    return
  }

  proxy.$modal.confirm('是否确认取消当前采集任务？').then(() => {
    cancelCollect(row.taskId).then(() => {
      proxy.$modal.msgSuccess('任务已取消')

      // 清理定时器
      if (pollTimers.value[row.databaseName]) {
        clearInterval(pollTimers.value[row.databaseName])
        delete pollTimers.value[row.databaseName]
      }

      // 更新状态
      const dbIndex = databaseList.value.findIndex(db => db.databaseName === row.databaseName)
      if (dbIndex !== -1) {
        databaseList.value[dbIndex].collecting = false
        databaseList.value[dbIndex].progress = {
          ...databaseList.value[dbIndex].progress,
          status: '已取消'
        }
      }
    }).catch(() => {
      proxy.$modal.msgError('取消任务失败')
    })
  }).catch(() => {})
}

// 采集数据表（单表采集）
function collectTable(row) {
  proxy.$modal.confirm(`是否确认采集数据表 "${row.tableName}" 的元数据？`).then(() => {
    // 设置加载状态
    const tableItem = tableList.value.find(t => t.tableName === row.tableName)
    if (tableItem) {
      tableItem.collecting = true
    }

    collectMetaTable({
      dataSourceId: dataSourceId.value,
      databaseName: selectedDatabase.value,
      tableName: row.tableName
    }).then(() => {
      proxy.$modal.msgSuccess('采集完成')
    }).catch(() => {
      proxy.$modal.msgError('采集失败')
    }).finally(() => {
      if (tableItem) {
        tableItem.collecting = false
      }
    })
  }).catch(() => {})
}

// 返回数据库列表
function backToDatabases() {
  selectedDatabase.value = ''
  selectedTable.value = ''
  tableList.value = []
}

// 返回数据源列表
function goBack() {
  router.push({ name: 'DataSource' })
}

// 获取数据库类型标签颜色
function getDbTypeTag(dbType) {
  const tagMap = {
    mysql: 'primary',
    postgresql: 'success',
    sqlite: 'info',
    oracle: 'warning',
    sqlserver: 'danger',
    presto: 'primary',
    starrocks: 'success'
  }
  return tagMap[dbType] || 'info'
}

// 重置所有状态
function resetState() {
  // 清理所有定时器
  Object.values(pollTimers.value).forEach(timer => clearInterval(timer))
  pollTimers.value = {}

  dataSourceInfo.value = {}
  databaseList.value = []
  tableList.value = []
  columnList.value = []
  selectedDatabase.value = ''
  selectedTable.value = ''
  databaseSearchText.value = ''
  tableSearchText.value = ''
  columnSearchText.value = ''
}

// 组件被 keep-alive 缓存激活时调用
onActivated(() => {
  console.log('数据源详情页面已激活')
  // 可以在这里恢复轮询或其他操作
  // 如果需要刷新数据，可以调用 loadDataSourceInfo()
})

// 组件被 keep-alive 缓存停用时调用
onDeactivated(() => {
  console.log('数据源详情页面已停用（缓存）')
  // 页面被缓存时，不清除状态和定时器
  // 这样切换回来时，采集进度仍然显示
})

// 组件卸载时清理定时器
onUnmounted(() => {
  console.log('数据源详情页面已卸载')
  Object.values(pollTimers.value).forEach(timer => clearInterval(timer))
  pollTimers.value = {}
})

// 监听路由参数变化
// watch(() => route.params.id, (newId, oldId) => {
//   if (newId && newId !== oldId) {
//     dataSourceId.value = newId
//     resetState()
//     loadDataSourceInfo()
//   }
// }, { immediate: true })

// 初始化
loadDataSourceInfo()
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.card-title-with-action {
  display: flex;
  align-items: center;
  gap: 16px;
}

.database-tag {
  font-size: 14px;
  padding: 8px 16px;
  height: auto;
}

.card-actions {
  display: flex;
  align-items: center;
}

.mt-20 {
  margin-top: 20px;
}

.prewrap {
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
