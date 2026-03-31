<!-- eslint-disable vue/no-v-model-argument -->
<template>
  <div class="app-container">
    <!-- 搜索�?-->
    <el-form v-if="showSearch" :model="queryParams" ref="queryRef" :inline="true">
      <el-form-item label="接口名称" prop="interfaceName">
        <el-input v-model="queryParams.interfaceName" placeholder="请输入接口名�? clearable style="width: 200px" @keyup.enter="getList" />
      </el-form-item>
      <el-form-item label="接口编码" prop="interfaceCode">
        <el-input v-model="queryParams.interfaceCode" placeholder="请输入接口编�? clearable style="width: 200px" @keyup.enter="getList" />
      </el-form-item>
      <el-form-item label="数据库类�? prop="interfaceDbType">
        <el-select v-model="queryParams.interfaceDbType" placeholder="请选择数据库类�? clearable style="width: 200px">
          <el-option v-for="item in dbTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="getList">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 工具�?-->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['dataservice:interface:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['dataservice:interface:remove']">删除</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-upload ref="uploadRef" action="#" :http-request="customUpload" :show-file-list="false" accept=".xlsx, .xls">
          <el-button type="info" plain icon="Upload" v-hasPermi="['dataservice:interface:import']">导入</el-button>
        </el-upload>
      </el-col>
      <el-col :span="1.5">
        <el-button type="success" plain icon="Download" :disabled="multiple" @click="handleExport" v-hasPermi="['dataservice:interface:export']">导出</el-button>
      </el-col>
      <right-toolbar :showSearch="showSearch" @update:showSearch="val => (showSearch = val)" @queryTable="getList" />
    </el-row>

    <!-- 列表 -->
    <el-table v-loading="loading" :data="dataList" @selection-change="handleSelectionChange" border>
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="接口名称" prop="interfaceName" width="200" :show-overflow-tooltip="true" />
      <el-table-column label="接口编码" prop="interfaceCode" width="200" :show-overflow-tooltip="true" />
      <el-table-column label="数据库类�? prop="interfaceDbType" width="120" />
      <el-table-column label="数据库名�? prop="interfaceDbName" :show-overflow-tooltip="true" />
      <el-table-column label="业务平台" prop="platformName" width="120" :show-overflow-tooltip="true" />
      <el-table-column label="模块名称" prop="moduleName" width="120" :show-overflow-tooltip="true" />
      <el-table-column label="报表名称" prop="reportName" width="120" :show-overflow-tooltip="true" />
      <el-table-column label="报表编码" prop="reportCode" width="120" :show-overflow-tooltip="true" />
      <el-table-column label="分页" prop="isPaging" width="80">
        <template #default="scope">
          <dict-tag :options="yes_no_options" :value="scope.row.isPaging" />
        </template>
      </el-table-column>
      <el-table-column label="日期查询" prop="isDateOption" width="100">
        <template #default="scope">
          <dict-tag :options="yes_no_options" :value="scope.row.isDateOption" />
        </template>
      </el-table-column>
      <el-table-column label="合计" prop="isTotal" width="80">
        <template #default="scope">
          <dict-tag :options="yes_no_options" :value="scope.row.isTotal" />
        </template>
      </el-table-column>
      <el-table-column label="登录验证" prop="isLoginVisit" width="100">
        <template #default="scope">
          <dict-tag :options="yes_no_options" :value="scope.row.isLoginVisit" />
        </template>
      </el-table-column>
      <el-table-column label="报警类型" prop="alarmType" width="120">
        <template #default="scope">
          <dict-tag :options="alarm_type_options" :value="scope.row.alarmType" />
        </template>
      </el-table-column>
      <el-table-column label="创建时间" align="center" prop="createTime" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="200" fixed="right">
        <template #default="scope">
          <el-button link size="small" type="primary" icon="View" @click="openDetail(scope.row)">明细</el-button>
          <el-button link size="small" type="primary" icon="Coin" @click="openExecute(scope.row)" v-hasPermi="['dataservice:interface:execute']">查询</el-button>
          <el-button link size="small" type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['dataservice:interface:edit']">修改</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      v-show="total > 0"
      :total="total"
      :page="queryParams.pageNum"
      :limit="queryParams.pageSize"
      @update:page="val => (queryParams.pageNum = val)"
      @update:limit="val => (queryParams.pageSize = val)"
      @pagination="getList"
    />

    <!-- 新增/修改弹窗 -->
    <InterfaceFormDialog
      v-model="open"
      :title="title"
      :form="form"
      :rules="rules"
      :datasource-options="datasourceOptions"
      @submit="submitForm"
      @cancel="cancel"
    />

    <!-- 执行查询弹窗 -->
    <InterfaceExecuteDialog
      v-model="execOpen"
      :exec-title="execTitle"
      :interface-id="execInterfaceId"
    />
  </div>
</template>

<script setup name="DataServiceInterface">
import { listInterfaceInfo, getInterfaceInfo, addInterfaceInfo, updateInterfaceInfo, delInterfaceInfo, exportInterfaceById, importInterfaceMeta } from '@/api/data/service'
import { listDatasource } from '@/api/data/datasource'
import { useRouter } from 'vue-router'
import InterfaceFormDialog from './InterfaceFormDialog.vue'
import InterfaceExecuteDialog from './InterfaceExecuteDialog.vue'
import { YES_NO_OPTIONS, ALARM_TYPE_OPTIONS, DB_TYPE_OPTIONS } from './constants'

const { proxy } = getCurrentInstance()
const router = useRouter()

const yes_no_options = YES_NO_OPTIONS
const alarm_type_options = ALARM_TYPE_OPTIONS
const dbTypeOptions = DB_TYPE_OPTIONS

const dataList = ref([])
const loading = ref(true)
const showSearch = ref(true)
const ids = ref([])
const single = ref(true)
const multiple = ref(true)
const total = ref(0)
const open = ref(false)
const title = ref('')
const datasourceOptions = ref([])
const execOpen = ref(false)
const execTitle = ref('执行查询')
const execInterfaceId = ref(null)

const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    interfaceName: undefined,
    interfaceCode: undefined,
    interfaceDbType: undefined
  },
  rules: {
    interfaceName: [{ required: true, message: '接口名称不能为空', trigger: 'blur' }],
    interfaceCode: [{ required: true, message: '接口编码不能为空', trigger: 'blur' }],
    interfaceDbType: [{ required: true, message: '数据库类型不能为�?, trigger: 'change' }],
    interfaceDbName: [{ required: true, message: '数据库名称不能为�?, trigger: 'blur' }]
  }
})

const { form, queryParams, rules } = toRefs(data)

function getList() {
  loading.value = true
  listInterfaceInfo(queryParams.value).then(response => {
    dataList.value = response.rows || []
    total.value = response.total || 0
  }).catch(() => {}).finally(() => { loading.value = false })
}

function resetQuery() {
  proxy.resetForm('queryRef')
  queryParams.value.pageNum = 1
  getList()
}

function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.interfaceId)
  single.value = selection.length !== 1
  multiple.value = selection.length === 0
}

function reset() {
  form.value = {
    interfaceId: undefined, reportId: undefined, interfaceName: undefined,
    interfaceCode: undefined, interfaceDesc: undefined, interfaceDbType: undefined,
    interfaceDbName: undefined, interfaceSql: undefined,
    isTotal: '0', totalSql: undefined, isPaging: '0',
    isDateOption: '0', isSecondTable: '0', isLoginVisit: '0',
    alarmType: '0', userName: undefined, interfaceDatasource: undefined,
    platformName: undefined, moduleName: undefined,
    reportCode: undefined, reportName: undefined
  }
  proxy.resetForm('formRef')
}

function cancel() {
  open.value = false
  reset()
}

function handleAdd() {
  reset()
  open.value = true
  title.value = '添加接口'
  loadDatasourceOptions()
}

function handleUpdate(row) {
  reset()
  const id = row?.interfaceId || ids.value
  getInterfaceInfo(id).then(response => {
    form.value = response.data || {}
    open.value = true
    title.value = '修改接口'
    loadDatasourceOptions()
  })
}

function submitForm() {
  const api = form.value.interfaceId !== undefined ? updateInterfaceInfo : addInterfaceInfo
  api(form.value).then(() => {
    proxy.$modal.msgSuccess(form.value.interfaceId !== undefined ? '修改成功' : '新增成功')
    open.value = false
    getList()
  })
}

function handleDelete(row) {
  const idsParam = row?.interfaceId || ids.value
  proxy.$modal.confirm('是否确认删除' + idsParam.length + '个数据项�?).then(function() {
    return delInterfaceInfo(idsParam)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

function customUpload(option) {
  const formData = new FormData()
  formData.append('file', option.file)
  proxy.$modal.loading('正在导入数据，请稍�?..')
  importInterfaceMeta(formData).then(res => {
    proxy.$modal.closeLoading()
    proxy.$modal.msgSuccess(res.msg)
    getList()
  }).catch(() => {
    proxy.$modal.closeLoading()
    proxy.$modal.msgError('导入失败')
  })
}

function handleExport() {
  if (ids.value.length === 0) {
    proxy.$modal.msgWarning('请先选择要导出的接口')
    return
  }
  if (ids.value.length > 10) {
    proxy.$modal.msgWarning('一次最多只能导�?0个接口，请减少选择数量')
    return
  }
  proxy.$modal.loading(`正在导出 ${ids.value.length} 个接口的元数据，请稍�?..`)
  let successCount = 0, failCount = 0
  const total = ids.value.length
  ids.value.forEach(id => {
    proxy.download('/dataservice/interface-info/' + id + '/export-meta', {}, `interface_${id}_meta.xlsx`)
      .then(() => { successCount++ })
      .catch(() => { failCount++ })
      .finally(() => {
        if (successCount + failCount === total) {
          proxy.$modal.closeLoading()
          if (failCount === 0) proxy.$modal.msgSuccess(`成功导出 ${successCount} 个接口元数据`)
          else proxy.$modal.msgWarning(`导出完成：成�?${successCount} 个，失败 ${failCount} 个`)
        }
      })
  })
}

function openDetail(row) {
  const id = row?.interfaceId
  if (!id) return
  router.push({ name: 'InterfaceDetail', params: { interfaceId: id } })
}

function openExecute(row) {
  execInterfaceId.value = row?.interfaceId
  execOpen.value = true
  execTitle.value = `执行查询 - ${row?.interfaceName || ''}`
}

function loadDatasourceOptions() {
  listDatasource().then(res => {
    datasourceOptions.value = res.rows || []
  })
}

getList()
</script>
