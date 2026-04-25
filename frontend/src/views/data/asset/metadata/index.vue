<template>
  <div class="app-container">
    <el-radio-group v-model="viewMode" style="margin-bottom: 16px" @change="handleViewModeChange">
      <el-radio-button label="table">表查找</el-radio-button>
      <el-radio-button label="column">字段查找</el-radio-button>
    </el-radio-group>

    <template v-if="viewMode === 'table'">
      <el-form :inline="true" style="margin-bottom: 12px">
        <el-form-item label="数据源">
          <el-select v-model="tableFilter.dataSourceId" placeholder="请选择数据源" clearable style="width: 180px" @change="handleDataSourceChange">
            <el-option v-for="ds in dataSourceList" :key="ds.dataSourceId" :label="ds.dataSourceName" :value="ds.dataSourceId" />
          </el-select>
        </el-form-item>
        <el-form-item label="表名">
          <el-input v-model="tableFilter.tableName" placeholder="支持模糊匹配" style="width: 180px" clearable />
        </el-form-item>
        <el-form-item label="数据库">
          <el-input v-model="tableFilter.databaseName" placeholder="支持模糊匹配" style="width: 180px" clearable />
        </el-form-item>
        <el-form-item label="资产分类">
          <el-select v-model="tableFilter.assetCategory" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="item in assetCategoryOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="数仓分层">
          <el-select v-model="tableFilter.warehouseLayer" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="item in warehouseLayerOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="业务域">
          <el-input v-model="tableFilter.businessDomain" placeholder="如 交易/会员" style="width: 160px" clearable />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="tableFilter.owner" placeholder="支持模糊匹配" style="width: 160px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="queryTables">查询</el-button>
          <el-button icon="Refresh" @click="resetTableFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="tableLoading" :data="tableList" row-key="id" style="width: 100%" fit border show-overflow-tooltip>
        <el-table-column prop="tableName" label="表名" min-width="150" />
        <el-table-column prop="comment" label="表描述" min-width="180">
          <template #default="scope"><div class="prewrap">{{ scope.row.comment || '-' }}</div></template>
        </el-table-column>
        <el-table-column prop="dataSourceName" label="数据源" width="140" />
        <el-table-column prop="databaseName" label="数据库" width="160" />
        <el-table-column label="资产分类" width="120">
          <template #default="scope"><el-tag size="small" effect="plain">{{ formatAssetCategory(scope.row.assetCategory) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="数仓分层" width="110">
          <template #default="scope"><span>{{ formatWarehouseLayer(scope.row.warehouseLayer) }}</span></template>
        </el-table-column>
        <el-table-column prop="businessDomain" label="业务域" width="140" />
        <el-table-column prop="subjectArea" label="主题域" width="140" />
        <el-table-column prop="owner" label="负责人" width="120" />
        <el-table-column label="安全等级" width="120">
          <template #default="scope"><el-tag size="small" :type="securityTagType(scope.row.securityLevel)" effect="plain">{{ formatSecurityLevel(scope.row.securityLevel) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column prop="updateTime" label="更新时间" width="180" />
        <el-table-column prop="createBy" label="采集人" width="100" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope"><el-button size="small" icon="View" @click="openColumns(scope.row)">查看列</el-button></template>
        </el-table-column>
      </el-table>

      <pagination v-model:page="tableQueryParams.pageNum" v-model:limit="tableQueryParams.pageSize" :total="tableTotal" @pagination="queryTables" />
    </template>

    <template v-else>
      <el-form :inline="true" style="margin-bottom: 12px">
        <el-form-item label="数据源">
          <el-select v-model="columnFilter.dataSourceId" placeholder="请选择数据源" clearable style="width: 180px">
            <el-option v-for="ds in dataSourceList" :key="ds.dataSourceId" :label="ds.dataSourceName" :value="ds.dataSourceId" />
          </el-select>
        </el-form-item>
        <el-form-item label="字段名">
          <el-input v-model="columnFilter.columnName" placeholder="支持模糊匹配" style="width: 160px" clearable />
        </el-form-item>
        <el-form-item label="字段描述">
          <el-input v-model="columnFilter.columnComment" placeholder="支持模糊匹配" style="width: 160px" clearable />
        </el-form-item>
        <el-form-item label="业务术语">
          <el-input v-model="columnFilter.businessTerm" placeholder="如 GMV/下单用户" style="width: 160px" clearable />
        </el-form-item>
        <el-form-item label="表名">
          <el-input v-model="columnFilter.tableName" placeholder="支持模糊匹配" style="width: 160px" clearable />
        </el-form-item>
        <el-form-item label="字段角色">
          <el-select v-model="columnFilter.warehouseRole" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="item in warehouseRoleOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="安全等级">
          <el-select v-model="columnFilter.securityLevel" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="item in securityLevelOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="queryColumns">查询</el-button>
          <el-button icon="Refresh" @click="resetColumnFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="columnLoading" :data="columnList" row-key="uniqueKey" style="width: 100%" fit border show-overflow-tooltip>
        <el-table-column prop="tableName" label="表名" min-width="150">
          <template #default="scope"><el-link type="primary" @click="goToTable(scope.row)">{{ scope.row.tableName }}</el-link></template>
        </el-table-column>
        <el-table-column prop="columnIndex" label="字段序号" width="80" align="center" />
        <el-table-column prop="columnName" label="字段名" min-width="120" />
        <el-table-column prop="columnComment" label="字段描述" min-width="150">
          <template #default="scope"><div class="prewrap">{{ scope.row.columnComment || '-' }}</div></template>
        </el-table-column>
        <el-table-column prop="businessTerm" label="业务术语" min-width="140" />
        <el-table-column prop="dataType" label="数据类型" width="120" />
        <el-table-column label="字段角色" width="120">
          <template #default="scope">{{ formatWarehouseRole(scope.row.warehouseRole) }}</template>
        </el-table-column>
        <el-table-column label="安全等级" width="120">
          <template #default="scope"><el-tag size="small" :type="securityTagType(scope.row.securityLevel)" effect="plain">{{ formatSecurityLevel(scope.row.securityLevel) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="standardCode" label="标准编码" width="140" />
        <el-table-column prop="metricUnit" label="指标单位" width="100" />
        <el-table-column prop="dataSourceName" label="数据源" width="120" />
        <el-table-column prop="databaseName" label="数据库" width="120" />
        <el-table-column prop="isPrimary" label="主键" width="80" align="center">
          <template #default="scope"><el-tag :type="scope.row.isPrimary ? 'success' : 'info'" size="small">{{ scope.row.isPrimary ? '是' : '否' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="isNullable" label="可空" width="80" align="center">
          <template #default="scope"><el-tag :type="scope.row.isNullable ? 'info' : 'warning'" size="small">{{ scope.row.isNullable ? '是' : '否' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="defaultValue" label="默认值" width="100" />
      </el-table>

      <pagination v-model:page="columnQueryParams.pageNum" v-model:limit="columnQueryParams.pageSize" :total="columnTotal" @pagination="queryColumns" />
    </template>

    <el-dialog title="字段详情" v-model="columnDialogVisible" width="80%" append-to-body>
      <el-table v-loading="columnDialogLoading" :data="currentColumns" border style="width: 100%">
        <el-table-column prop="columnIndex" label="字段序号" width="80" align="center" />
        <el-table-column prop="columnName" label="字段名" min-width="120" />
        <el-table-column prop="dataType" label="数据类型" width="120" />
        <el-table-column prop="columnComment" label="字段描述" min-width="150">
          <template #default="scope"><div class="prewrap">{{ scope.row.columnComment || '-' }}</div></template>
        </el-table-column>
        <el-table-column prop="businessTerm" label="业务术语" min-width="140" />
        <el-table-column label="字段角色" width="120">
          <template #default="scope">{{ formatWarehouseRole(scope.row.warehouseRole) }}</template>
        </el-table-column>
        <el-table-column label="安全等级" width="120">
          <template #default="scope"><el-tag size="small" :type="securityTagType(scope.row.securityLevel)" effect="plain">{{ formatSecurityLevel(scope.row.securityLevel) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="standardCode" label="标准编码" width="140" />
        <el-table-column prop="metricUnit" label="指标单位" width="100" />
        <el-table-column prop="isPrimary" label="主键" width="80" align="center">
          <template #default="scope"><el-tag :type="scope.row.isPrimary ? 'success' : 'info'" size="small">{{ scope.row.isPrimary ? '是' : '否' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="isNullable" label="可空" width="80" align="center">
          <template #default="scope"><el-tag :type="scope.row.isNullable ? 'info' : 'warning'" size="small">{{ scope.row.isNullable ? '是' : '否' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="defaultValue" label="默认值" width="100" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup name="DataAssetMetadata">
import { listDatasource } from '@/api/data/datasource'
import { listMetaTables, listMetaColumns } from '@/api/data/asset'

const { proxy } = getCurrentInstance()

const assetCategoryOptions = [
  { label: '源端元数据', value: 'source' },
  { label: '业务元数据', value: 'business' },
  { label: '数仓元数据', value: 'warehouse' },
  { label: '服务资产', value: 'service' },
  { label: '其他资产', value: 'other' },
]
const warehouseLayerOptions = [
  { label: '源端', value: 'SOURCE' },
  { label: 'ODS', value: 'ODS' },
  { label: 'DWD', value: 'DWD' },
  { label: 'DWS', value: 'DWS' },
  { label: 'ADS', value: 'ADS' },
  { label: 'DIM', value: 'DIM' },
]
const warehouseRoleOptions = [
  { label: '维度字段', value: 'dimension' },
  { label: '指标字段', value: 'measure' },
  { label: '分区字段', value: 'partition_key' },
  { label: '业务主键', value: 'business_key' },
  { label: '属性字段', value: 'attribute' },
]
const securityLevelOptions = [
  { label: '公开', value: 'public' },
  { label: '内部', value: 'internal' },
  { label: '敏感', value: 'sensitive' },
  { label: '严格受限', value: 'restricted' },
]

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
  databaseName: null,
  assetCategory: null,
  warehouseLayer: null,
  businessDomain: null,
  owner: null,
})
const columnFilter = ref({
  dataSourceId: null,
  columnName: null,
  columnComment: null,
  businessTerm: null,
  tableName: null,
  warehouseRole: null,
  securityLevel: null,
  standardCode: null,
})
const tableQueryParams = ref({ pageNum: 1, pageSize: 10 })
const columnQueryParams = ref({ pageNum: 1, pageSize: 10 })

const columnDialogVisible = ref(false)
const columnDialogLoading = ref(false)
const currentColumns = ref([])

function formatByOptions(options, value, fallback = '-') {
  return options.find(item => item.value === value)?.label || value || fallback
}
function formatAssetCategory(value) {
  return formatByOptions(assetCategoryOptions, value)
}
function formatWarehouseLayer(value) {
  return formatByOptions(warehouseLayerOptions, value)
}
function formatWarehouseRole(value) {
  return formatByOptions(warehouseRoleOptions, value)
}
function formatSecurityLevel(value) {
  return formatByOptions(securityLevelOptions, value, '内部')
}
function securityTagType(value) {
  return {
    public: 'success',
    internal: 'info',
    sensitive: 'warning',
    restricted: 'danger',
  }[value] || 'info'
}

function loadDataSources() {
  listDatasource({ pageNum: 1, pageSize: 1000, status: '0' }).then(response => {
    dataSourceList.value = response.rows || []
  })
}

function handleViewModeChange() {
  if (viewMode.value === 'table') {
    queryTables()
  } else {
    queryColumns()
  }
}

function queryTables() {
  tableLoading.value = true
  const params = { ...tableQueryParams.value, ...tableFilter.value }
  listMetaTables(params).then(response => {
    tableList.value = response.rows || []
    tableTotal.value = response.total || 0
    tableLoading.value = false
  }).catch(() => {
    tableLoading.value = false
  })
}

function queryColumns() {
  columnLoading.value = true
  const params = { ...columnQueryParams.value, ...columnFilter.value }
  listMetaColumns(params).then(response => {
    columnList.value = (response.rows || []).map((item, index) => ({
      ...item,
      uniqueKey: `${item.tableId}-${item.columnName}-${index}`,
    }))
    columnTotal.value = response.total || 0
    columnLoading.value = false
  }).catch(() => {
    columnLoading.value = false
  })
}

function resetTableFilters() {
  tableFilter.value = {
    dataSourceId: null,
    tableName: null,
    databaseName: null,
    assetCategory: null,
    warehouseLayer: null,
    businessDomain: null,
    owner: null,
  }
  tableQueryParams.value.pageNum = 1
  queryTables()
}

function resetColumnFilters() {
  columnFilter.value = {
    dataSourceId: null,
    columnName: null,
    columnComment: null,
    businessTerm: null,
    tableName: null,
    warehouseRole: null,
    securityLevel: null,
    standardCode: null,
  }
  columnQueryParams.value.pageNum = 1
  queryColumns()
}

function openColumns(row) {
  columnDialogVisible.value = true
  columnDialogLoading.value = true
  listMetaColumns({
    dataSourceId: row.dataSourceId,
    tableName: row.tableName,
    databaseName: row.databaseName,
  }).then(response => {
    currentColumns.value = response.rows || []
    columnDialogLoading.value = false
  }).catch(() => {
    columnDialogLoading.value = false
  })
}

function goToTable(row) {
  tableFilter.value.dataSourceId = row.dataSourceId
  tableFilter.value.tableName = row.tableName
  tableFilter.value.databaseName = row.databaseName
  viewMode.value = 'table'
  queryTables()
}

function handleDataSourceChange() {
  tableQueryParams.value.pageNum = 1
  queryTables()
}

loadDataSources()
queryTables()
</script>

<style scoped>
.prewrap {
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
