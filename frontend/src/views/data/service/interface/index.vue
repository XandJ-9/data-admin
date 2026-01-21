<!-- eslint-disable vue/no-v-model-argument -->
<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <el-form v-if="showSearch" :model="queryParams" ref="queryRef" :inline="true">
      <el-form-item label="接口名称" prop="interfaceName">
        <el-input v-model="queryParams.interfaceName" placeholder="请输入接口名称" clearable style="width: 200px" @keyup.enter="getList" />
      </el-form-item>
      <el-form-item label="接口编码" prop="interfaceCode">
        <el-input v-model="queryParams.interfaceCode" placeholder="请输入接口编码" clearable style="width: 200px" @keyup.enter="getList" />
      </el-form-item>
      <el-form-item label="数据库类型" prop="interfaceDbType">
        <el-select v-model="queryParams.interfaceDbType" placeholder="请选择数据库类型" clearable style="width: 200px">
          <el-option v-for="item in dbTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="getList">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 工具栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['dataservice:interface:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <!-- <el-button type="success" plain icon="Edit" :disabled="single" @click="handleUpdate" v-hasPermi="['dataservice:interface:edit']">修改</el-button> -->
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['dataservice:interface:remove']">删除</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-upload
          ref="uploadRef"
          action="#"
          :http-request="customUpload"
          :show-file-list="false"
          accept=".xlsx, .xls"
        >
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
      <el-table-column label="数据库类型" prop="interfaceDbType" width="120" />
      <el-table-column label="数据库名称" prop="interfaceDbName" :show-overflow-tooltip="true" />
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
          <!-- <el-button link size="small" type="danger" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['dataservice:interface:remove']">删除</el-button> -->
          <!-- <el-button link size="small" type="warning" icon="Download" @click="handleExport(scope.row)" v-hasPermi="['dataservice:interface:export']">导出数据</el-button> -->
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
    <el-dialog :title="title" v-model="open" width="900px" append-to-body>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="140px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="接口名称" prop="interfaceName">
              <el-input v-model="form.interfaceName" placeholder="请输入接口名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="接口编码" prop="interfaceCode">
              <el-input v-model="form.interfaceCode" placeholder="请输入接口编码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据库类型" prop="interfaceDbType">
              <el-select v-model="form.interfaceDbType" placeholder="请选择数据库类型">
                <el-option v-for="item in dbTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据库名称" prop="interfaceDbName">
              <el-input v-model="form.interfaceDbName" placeholder="请输入数据库名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据源" prop="interfaceDatasource">
              <el-select v-model="form.interfaceDatasource" filterable placeholder="请选择数据源">
                <el-option v-for="ds in datasourceOptions" :key="ds.dataSourceId" :label="ds.dataSourceName" :value="ds.dataSourceId" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否分页" prop="isPaging">
              <el-radio-group v-model="form.isPaging">
                <el-radio v-for="dict in yes_no_options" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否日期查询" prop="isDateOption">
              <el-radio-group v-model="form.isDateOption">
                <el-radio v-for="dict in yes_no_options" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否合计" prop="isTotal">
              <el-radio-group v-model="form.isTotal">
                <el-radio v-for="dict in yes_no_options" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否二级表头" prop="isSecondTable">
              <el-radio-group v-model="form.isSecondTable">
                <el-radio v-for="dict in yes_no_options" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="登录校验" prop="isLoginVisit">
              <el-radio-group v-model="form.isLoginVisit">
                <el-radio v-for="dict in yes_no_options" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="报警类型" prop="alarmType">
              <el-select v-model="form.alarmType" placeholder="请选择报警类型">
                <el-option v-for="dict in alarm_type_options" :key="dict.value" :label="dict.label" :value="dict.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="接口状态" prop="enable">
              <el-select v-model="form.enable" placeholder="请选择接口状态">
                <el-option v-for="dict in enable_options" :key="dict.value" :label="dict.label" :value="dict.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="接口描述" prop="interfaceDesc">
              <el-input v-model="form.interfaceDesc" type="textarea" :rows="2" placeholder="请输入接口描述" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="接口SQL" prop="interfaceSql">
              <el-input v-model="form.interfaceSql" type="textarea" :rows="5" placeholder="请输入接口 SQL（支持模板渲染）" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="合计SQL" prop="totalSql">
              <el-input v-model="form.totalSql" type="textarea" :rows="3" placeholder="可选：合计 SQL" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="业务平台" prop="platformName">
              <el-input v-model="form.platformName" placeholder="请输入业务平台" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模块名称" prop="moduleName">
              <el-input v-model="form.moduleName" placeholder="请输入模块名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="报表编码" prop="reportCode">
              <el-input v-model="form.reportCode" placeholder="请输入报表编码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="报表名称" prop="reportName">
              <el-input v-model="form.reportName" placeholder="请输入报表名称" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 执行查询弹窗 -->
    <el-dialog :title="execTitle" v-model="execOpen" width="900px" append-to-body>
      <el-form label-width="120px">
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="参数(JSON)">
              <el-input v-model="execForm.paramsJson" type="textarea" :rows="5" placeholder='例如: {&#10;  "startDate": "2024-01-01",&#10;  "endDate": "2024-12-31"&#10;}' />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="每页条数">
              <el-input-number v-model="execForm.pageSize" :min="1" :max="5000" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="偏移量">
              <el-input-number v-model="execForm.offset" :min="0" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <el-divider />
      <el-table v-loading="execLoading" :data="execRows" height="300px" style="width: 100%">
        <el-table-column v-for="col in execColumns" :key="col" :prop="col" :label="col" :show-overflow-tooltip="true" />
      </el-table>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="runExecute">执行查询</el-button>
          <el-button type="warning" @click="exportFromDialog">导出数据</el-button>
          <el-button @click="execOpen = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
  
</template>

<script setup name="Interface">
/* eslint-disable vue/no-v-model-argument */
import { listInterfaceInfo, getInterfaceInfo, addInterfaceInfo, updateInterfaceInfo, delInterfaceInfo, executeInterfaceById, exportInterfaceById, importInterfaceMeta } from '@/api/data/service'
import { listDatasource } from '@/api/data/source'
import { useRouter } from 'vue-router'

const { proxy } = getCurrentInstance()
const router = useRouter()
const { sys_normal_disable } = proxy.useDict('sys_normal_disable')

const yes_no_options = [
  { value: '1', label: '是' },
  { value: '0', label: '否' },
]

const enable_options = [
  { value: '1', label: '启用' },
  { value: '0', label: '禁用' },
]
const alarm_type_options = [
  { value: '0', label: '否' },
  { value: '1', label: '邮件' },
  { value: '2', label: '短信' },
  { value: '3', label: '钉钉' },
  { value: '4', label: '企业微信' },
  { value: '5', label: '电话' },
  { value: '6', label: '飞书' },
]

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

// 导入相关
const uploadRef = ref(null)

function customUpload(option) {
  const formData = new FormData()
  formData.append('file', option.file)
  proxy.$modal.loading("正在导入数据，请稍候...")
  importInterfaceMeta(formData).then(res => {
    proxy.$modal.closeLoading()
    proxy.$modal.msgSuccess(res.msg)
    getList()
  }).catch(() => {
    proxy.$modal.closeLoading()
    proxy.$modal.msgError('导入失败')
  })
}

// 导出接口信息
function handleExport() {
    // 验证是否选择了接口
    if (ids.value.length == 0) {
        proxy.$modal.msgWarning('请先选择要导出的接口')
        return
    }

    // 验证导出数量
    if (ids.value.length > 10) {
        proxy.$modal.msgWarning('一次最多只能导出10个接口，请减少选择数量')
        return
    }

    // 显示加载提示
    proxy.$modal.loading(`正在导出 ${ids.value.length} 个接口的元数据，请稍候...`)

    // 执行导出
    let successCount = 0
    let failCount = 0
    const total = ids.value.length

    ids.value.forEach(id => {
        proxy.download('/dataservice/interface-info/' + id + '/export-meta', {}, `interface_${id}_meta.xlsx`)
            .then(() => {
                successCount++
            })
            .catch(() => {
                failCount++
            })
            .finally(() => {
                // 当所有导出请求完成后
                if (successCount + failCount === total) {
                    proxy.$modal.closeLoading()
                    if (failCount === 0) {
                        proxy.$modal.msgSuccess(`成功导出 ${successCount} 个接口元数据`)
                    } else {
                        proxy.$modal.msgWarning(`导出完成：成功 ${successCount} 个，失败 ${failCount} 个`)
                    }
                }
            })
    })
}

// 执行查询弹窗与结果
const execOpen = ref(false)
const execTitle = ref('执行查询')
const execLoading = ref(false)
const execForm = ref({ interfaceId: undefined, paramsJson:undefined, pageSize: 50, offset: 0 })
const execRows = ref([])
const execColumns = ref([])

const dbTypeOptions = ref([
  { value: 'mysql', label: 'MySQL' },
  { value: 'postgres', label: 'PostgreSQL' },
  { value: 'presto', label: 'Presto' },
  { value: 'trino', label: 'Trino' },
  { value: 'starrocks', label: 'StarRocks' },
])

const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    interfaceName: undefined,
    interfaceCode: undefined,
    interfaceDbType: undefined,
  },
  rules: {
    interfaceName: [{ required: true, message: '接口名称不能为空', trigger: 'blur' }],
    interfaceCode: [{ required: true, message: '接口编码不能为空', trigger: 'blur' }],
    interfaceDbType: [{ required: true, message: '数据库类型不能为空', trigger: 'change' }],
    interfaceDbName: [{ required: true, message: '数据库名称不能为空', trigger: 'blur' }],
  },
})

const { form, queryParams, rules } = toRefs(data)

function getList() {
  loading.value = true
  listInterfaceInfo(queryParams.value).then(response => {
    dataList.value = response.rows || []
    total.value = response.total || 0
    loading.value = false
  }).catch(() => {
    loading.value = false
  })
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
    interfaceId: undefined,
    reportId: undefined,
    interfaceName: undefined,
    interfaceCode: undefined,
    interfaceDesc: undefined,
    interfaceDbType: undefined,
    interfaceDbName: undefined,
    interfaceSql: undefined,
    isTotal: '0',
    totalSql: undefined,
    isPaging: '0',
    isDateOption: '0',
    isSecondTable: '0',
    isLoginVisit: '0',
    alarmType: '0',
    userName: undefined,
    interfaceDatasource: undefined,
    platformName: undefined,
    moduleName: undefined,
    reportCode: undefined,
    reportName: undefined,
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
  proxy.$refs['formRef'].validate(valid => {
    if (!valid) return
    if (form.value.interfaceId !== undefined) {
      updateInterfaceInfo(form.value).then(() => {
        proxy.$modal.msgSuccess('修改成功')
        open.value = false
        getList()
      })
    } else {
      addInterfaceInfo(form.value).then(() => {
        proxy.$modal.msgSuccess('新增成功')
        open.value = false
        getList()
      })
    }
  })
}

function handleDelete(row) {
  const idsParam = row?.interfaceId || ids.value
  proxy.$modal.confirm('是否确认删除' + idsParam.length + '个数据项？').then(function() {
    return delInterfaceInfo(idsParam)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

function openDetail(row) {
  const id = row?.interfaceId
  if (!id) return
    //   router.push('/dataservice/interface/detail/' + id)
    router.push({ name: 'InterfaceDetail', params: { interfaceId: id } })
}

function loadDatasourceOptions() {
  listDatasource().then(res => {
    datasourceOptions.value = res.rows || []
  })
}

function openExecute(row) {
  execRows.value = []
  execColumns.value = []
  execForm.value.interfaceId = row?.interfaceId
  execOpen.value = true
  execTitle.value = `执行查询 - ${row?.interfaceName || ''}`
}

function runExecute() {
  const id = execForm.value.interfaceId
  if (!id) return
  let paramsObj = null
  if (execForm.value.paramsJson && execForm.value.paramsJson.trim()) {
    try {
      paramsObj = JSON.parse(execForm.value.paramsJson)
    } catch (e) {
      proxy.$modal.msgError('参数JSON格式错误')
      return
    }
  }
  execLoading.value = true
  executeInterfaceById(id, { params: paramsObj || {}, pageSize: execForm.value.pageSize, offset: execForm.value.offset }).then(res => {
      const rows = res.data?.rows
      execColumns.value = res.data?.columns || []
      execRows.value = rows.map(item => {
          const rowObj = {}
          execColumns.value.forEach((col, index) => {
              rowObj[col] = item[index]
          })
          return rowObj
      })
  }).catch(err => {
    proxy.$modal.msgError(err?.msg || '执行失败')
  }).finally(() => {
    execLoading.value = false
  })
}

function exportFromDialog() {
  const id = execForm.value.interfaceId
  if (!id) return
  let paramsObj = null
  if (execForm.value.paramsJson && execForm.value.paramsJson.trim()) {
    try {
      paramsObj = JSON.parse(execForm.value.paramsJson)
    } catch (e) {
      // 使用空参数
      paramsObj = null
    }
  }
  exportInterfaceById(id, { params: paramsObj || {}, pageSize: execForm.value.pageSize || 1000, offset: execForm.value.offset || 0 }).then(res => {
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `interface_${id}_export.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    proxy.$modal.msgSuccess('导出成功')
  }).catch(err => {
    proxy.$modal.msgError(err?.msg || '导出失败')
  })
}

getList()
</script>

<style scoped>
.mb8 { margin-bottom: 8px; }
.prewrap { white-space: pre-wrap; word-break: break-word; }
</style>