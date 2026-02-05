<template>
  <div class="app-container">
    <!-- 视图切换 -->
    <el-radio-group v-model="viewMode" style="margin-bottom: 16px" @change="handleViewModeChange">
      <el-radio-button label="table">表查找</el-radio-button>
      <el-radio-button label="column">字段查找</el-radio-button>
    </el-radio-group>

    <!-- 表查找模式 -->
    <template v-if="viewMode === 'table'">
      <el-form :inline="true" style="margin-bottom: 12px">
        <el-form-item label="数据源">
          <el-select v-model="tableFilter.dataSourceId" placeholder="请选择数据源" clearable style="width: 200px" @change="handleDataSourceChange">
            <el-option
              v-for="ds in dataSourceList"
              :key="ds.dataSourceId"
              :label="ds.dataSourceName"
              :value="ds.dataSourceId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="表名">
          <el-input v-model="tableFilter.tableName" placeholder="支持模糊匹配" style="width: 200px" clearable />
        </el-form-item>
        <el-form-item label="数据库">
          <el-input v-model="tableFilter.databaseName" placeholder="支持模糊匹配" style="width: 200px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="queryTables">查询</el-button>
          <el-button icon="Refresh" @click="resetTableFilters">重置</el-button>
          <el-button type="primary" icon="Collection" @click="showCollectionDialog">元数据采集</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="tableLoading"
        :data="tableList"
        row-key="id"
        style="width: 100%"
        fit
        border
        show-overflow-tooltip
      >
        <el-table-column prop="tableName" label="表名" min-width="150" />
        <el-table-column prop="comment" label="表描述" min-width="200">
          <template #default="scope">
            <div class="prewrap">{{ scope.row.comment || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="dataSourceName" label="数据源" width="150" />
        <el-table-column prop="databaseName" label="数据库" width="150" />
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column prop="updateTime" label="更新时间" width="180" />
        <el-table-column prop="createBy" label="采集人" width="100" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button size="small" icon="View" @click="openColumns(scope.row)">查看列</el-button>
          </template>
        </el-table-column>
      </el-table>

      <pagination
        v-model:page="tableQueryParams.pageNum"
        v-model:limit="tableQueryParams.pageSize"
        :total="tableTotal"
        @pagination="queryTables"
      />
    </template>

    <!-- 字段查找模式 -->
    <template v-else>
      <el-form :inline="true" style="margin-bottom: 12px">
        <el-form-item label="数据源">
          <el-select v-model="columnFilter.dataSourceId" placeholder="请选择数据源" clearable style="width: 200px">
            <el-option
              v-for="ds in dataSourceList"
              :key="ds.dataSourceId"
              :label="ds.dataSourceName"
              :value="ds.dataSourceId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="字段名">
          <el-input v-model="columnFilter.columnName" placeholder="支持模糊匹配" style="width: 180px" clearable />
        </el-form-item>
        <el-form-item label="字段描述">
          <el-input v-model="columnFilter.columnComment" placeholder="支持模糊匹配" style="width: 180px" clearable />
        </el-form-item>
        <el-form-item label="表名">
          <el-input v-model="columnFilter.tableName" placeholder="支持模糊匹配" style="width: 180px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="queryColumns">查询</el-button>
          <el-button icon="Refresh" @click="resetColumnFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="columnLoading"
        :data="columnList"
        row-key="uniqueKey"
        style="width: 100%"
        fit
        border
        show-overflow-tooltip
      >
        <el-table-column prop="tableName" label="表名" min-width="150">
          <template #default="scope">
            <el-link type="primary" @click="goToTable(scope.row)">{{ scope.row.tableName }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="columnIndex" label="字段序号" width="80" align="center" />
        <el-table-column prop="columnName" label="字段名" min-width="120" />
        <el-table-column prop="columnComment" label="字段描述" min-width="150">
          <template #default="scope">
            <div class="prewrap">{{ scope.row.columnComment || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="dataType" label="数据类型" width="120" />
        <el-table-column prop="dataSourceName" label="数据源" width="120" />
        <el-table-column prop="databaseName" label="数据库" width="120" />
        <el-table-column prop="isPrimary" label="主键" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.isPrimary ? 'success' : 'info'" size="small">
              {{ scope.row.isPrimary ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isNullable" label="可空" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.isNullable ? 'info' : 'warning'" size="small">
              {{ scope.row.isNullable ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="defaultValue" label="默认值" width="100" />
      </el-table>

      <pagination
        v-model:page="columnQueryParams.pageNum"
        v-model:limit="columnQueryParams.pageSize"
        :total="columnTotal"
        @pagination="queryColumns"
      />
    </template>

    <!-- 字段详情对话框 -->
    <el-dialog title="字段详情" v-model="columnDialogVisible" width="80%" append-to-body>
      <el-table
        v-loading="columnDialogLoading"
        :data="currentColumns"
        border
        style="width: 100%"
      >
        <el-table-column prop="columnIndex" label="字段序号" width="80" align="center" />
        <el-table-column prop="columnName" label="字段名" min-width="120" />
        <el-table-column prop="dataType" label="数据类型" width="120" />
        <el-table-column prop="columnComment" label="字段描述" min-width="150">
          <template #default="scope">
            <div class="prewrap">{{ scope.row.columnComment || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="isPrimary" label="主键" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.isPrimary ? 'success' : 'info'" size="small">
              {{ scope.row.isPrimary ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isNullable" label="可空" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.isNullable ? 'info' : 'warning'" size="small">
              {{ scope.row.isNullable ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="defaultValue" label="默认值" width="100" />
      </el-table>
    </el-dialog>

    <!-- 元数据采集对话框 -->
    <el-dialog title="元数据采集" v-model="collectionDialogVisible" width="600px" append-to-body>
      <el-form :model="collectionForm" label-width="100px">
        <el-form-item label="数据源">
          <el-select v-model="collectionForm.dataSourceId" placeholder="请选择数据源" style="width: 100%">
            <el-option
              v-for="ds in dataSourceList"
              :key="ds.dataSourceId"
              :label="ds.dataSourceName"
              :value="ds.dataSourceId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数据库">
          <el-input v-model="collectionForm.databaseName" placeholder="可选，留空则采集所有数据库" />
        </el-form-item>
        <el-form-item label="采集方式">
          <el-radio-group v-model="collectionForm.async">
            <el-radio :label="false">同步采集</el-radio>
            <el-radio :label="true">异步采集</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="collectionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="collectionLoading" @click="handleCollection">开始采集</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="DataAssetMetadata">
import {
  listDatasource,
  listMetaTables,
  listMetaColumns,
  listTables,
  listColumns,
  collectMeta,
  collectMetaAsync,
  getCollectStatus
} from '@/api/data/asset'

const { proxy } = getCurrentInstance()

const viewMode = ref('table')
const tableLoading = ref(false)
const columnLoading = ref(false)
const tableList = ref([])
const columnList = ref([])
const tableTotal = ref(0)
const columnTotal = ref(0)
const dataSourceList = ref([])

const tableFilter = ref({
  dataSourceId: null,
  tableName: null,
  databaseName: null
})

const columnFilter = ref({
  dataSourceId: null,
  columnName: null,
  columnComment: null,
  tableName: null
})

const tableQueryParams = ref({
  pageNum: 1,
  pageSize: 10
})

const columnQueryParams = ref({
  pageNum: 1,
  pageSize: 10
})

const columnDialogVisible = ref(false)
const columnDialogLoading = ref(false)
const currentColumns = ref([])

const collectionDialogVisible = ref(false)
const collectionLoading = ref(false)
const collectionForm = ref({
  dataSourceId: null,
  databaseName: '',
  async: false
})

// 加载数据源列表
function loadDataSources() {
  listDatasource({ pageNum: 1, pageSize: 1000, status: '0' }).then(response => {
    dataSourceList.value = response.rows
  })
}

// 视图模式切换
function handleViewModeChange() {
  if (viewMode.value === 'table') {
    queryTables()
  } else {
    queryColumns()
  }
}

// 查询表
function queryTables() {
  tableLoading.value = true
  const params = {
    ...tableQueryParams.value,
    ...tableFilter.value
  }
  listMetaTables(params).then(response => {
    tableList.value = response.rows
    tableTotal.value = response.total
    tableLoading.value = false
  }).catch(() => {
    tableLoading.value = false
  })
}

// 查询字段
function queryColumns() {
  columnLoading.value = true
  const params = {
    ...columnQueryParams.value,
    ...columnFilter.value
  }
  // 映射前端参数名到后端
  if (params.columnName) params.columnName = params.columnName
  if (params.columnComment) params.columnComment = params.columnComment
  if (params.tableName) params.tableName = params.tableName

  listMetaColumns(params).then(response => {
    columnList.value = response.rows.map((item, index) => ({
      ...item,
      uniqueKey: `${item.tableId}-${item.columnName}-${index}`
    }))
    columnTotal.value = response.total
    columnLoading.value = false
  }).catch(() => {
    columnLoading.value = false
  })
}

// 重置表筛选
function resetTableFilters() {
  tableFilter.value = {
    dataSourceId: null,
    tableName: null,
    databaseName: null
  }
  tableQueryParams.value.pageNum = 1
  queryTables()
}

// 重置字段筛选
function resetColumnFilters() {
  columnFilter.value = {
    dataSourceId: null,
    columnName: null,
    columnComment: null,
    tableName: null
  }
  columnQueryParams.value.pageNum = 1
  queryColumns()
}

// 打开字段详情
function openColumns(row) {
  columnDialogVisible.value = true
  columnDialogLoading.value = true
  listColumns({
    dataSourceId: row.dataSourceId,
    tableName: row.tableName,
    databaseName: row.databaseName
  }).then(response => {
    currentColumns.value = response.rows
    columnDialogLoading.value = false
  }).catch(() => {
    columnDialogLoading.value = false
  })
}

// 跳转到表
function goToTable(row) {
  tableFilter.value.dataSourceId = row.dataSourceId
  tableFilter.value.tableName = row.tableName
  tableFilter.value.databaseName = row.databaseName
  viewMode.value = 'table'
  queryTables()
}

// 数据源变化
function handleDataSourceChange() {
  tableQueryParams.value.pageNum = 1
  queryTables()
}

// 显示采集对话框
function showCollectionDialog() {
  collectionDialogVisible.value = true
  collectionForm.value = {
    dataSourceId: tableFilter.value.dataSourceId || null,
    databaseName: '',
    async: false
  }
}

// 执行采集
function handleCollection() {
  if (!collectionForm.value.dataSourceId) {
    proxy.$modal.msgWarning('请选择数据源')
    return
  }

  collectionLoading.value = true
  const data = {
    dataSourceId: collectionForm.value.dataSourceId,
    databaseName: collectionForm.value.databaseName
  }

  const action = collectionForm.value.async ? collectMetaAsync : collectMeta

  action(data).then(response => {
    collectionLoading.value = false
    if (collectionForm.value.async) {
      proxy.$modal.msgSuccess(`采集任务已启动，任务ID: ${response.data.taskId}`)
      // 可以在这里实现轮询任务状态
    } else {
      proxy.$modal.msgSuccess('采集完成')
      queryTables()
    }
    collectionDialogVisible.value = false
  }).catch(() => {
    collectionLoading.value = false
  })
}

// 初始化
loadDataSources()
queryTables()
</script>

<style scoped>
.prewrap {
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
