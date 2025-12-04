<!-- eslint-disable vue/no-v-model-argument -->
<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <el-form :model="queryParams" ref="queryRef" :inline="true">
      <el-form-item label="接口名称" prop="interfaceName">
        <el-input v-model="queryParams.interfaceName" placeholder="请输入接口名称" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="接口编码" prop="interfaceCode">
        <el-input v-model="queryParams.interfaceCode" placeholder="请输入接口编码" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="数据库类型" prop="interfaceDbType">
        <el-select v-model="queryParams.interfaceDbType" placeholder="请选择数据库类型" clearable style="width: 200px">
          <el-option v-for="item in dbTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 工具栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['dataservice:interface:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="success" plain icon="Edit" :disabled="single" @click="handleUpdate" v-hasPermi="['dataservice:interface:edit']">修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['dataservice:interface:remove']">删除</el-button>
      </el-col>
      <right-toolbar :showSearch="showSearch" @update:showSearch="val => (showSearch = val)" @queryTable="getList" />
    </el-row>

    <!-- 列表 -->
    <el-table v-loading="loading" :data="dataList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="接口名称" prop="interfaceName" :show-overflow-tooltip="true" />
      <el-table-column label="接口编码" prop="interfaceCode" :show-overflow-tooltip="true" />
      <el-table-column label="数据库类型" prop="interfaceDbType" width="120" />
      <el-table-column label="数据库名称" prop="interfaceDbName" :show-overflow-tooltip="true" />
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
      <el-table-column label="操作" align="center" width="250" fixed="right">
        <template #default="scope">
          <el-button link type="primary" icon="View" @click="openDetail(scope.row)">查看明细</el-button>
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['dataservice:interface:edit']">修改</el-button>
          <el-button link type="danger" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['dataservice:interface:remove']">删除</el-button>
          <!-- <el-divider direction="vertical" /> -->
          <!-- 换行 -->
          <br />
          <el-button link type="success" icon="Link" @click="handleTest(scope.row)" v-hasPermi="['dataservice:interface:test']">测试连接</el-button>
          <el-button link type="primary" icon="Coin" @click="openExecute(scope.row)" v-hasPermi="['dataservice:interface:execute']">执行查询</el-button>
          <el-button link type="warning" icon="Download" @click="handleExport(scope.row)" v-hasPermi="['dataservice:interface:export']">导出数据</el-button>
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
        </el-row>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 明细抽屉：接口信息 + 字段列表 -->
    <el-drawer v-model="detailOpen" title="接口明细" size="80%" append-to-body>
      <div style="margin-bottom: 12px;">
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="接口名称">{{ detail.interfaceName }}</el-descriptions-item>
          <el-descriptions-item label="接口编码">{{ detail.interfaceCode }}</el-descriptions-item>
          <el-descriptions-item label="数据库类型">{{ detail.interfaceDbType }}</el-descriptions-item>
          <el-descriptions-item label="数据库名称">{{ detail.interfaceDbName }}</el-descriptions-item>
          <el-descriptions-item label="分页"><dict-tag :options="yes_no_options" :value="detail.isPaging" /></el-descriptions-item>
          <el-descriptions-item label="日期查询"><dict-tag :options="yes_no_options" :value="detail.isDateOption" /></el-descriptions-item>
          <el-descriptions-item label="合计"><dict-tag :options="yes_no_options" :value="detail.isTotal" /></el-descriptions-item>
          <el-descriptions-item label="登录验证"><dict-tag :options="yes_no_options" :value="detail.isLoginVisit" /></el-descriptions-item>
          <el-descriptions-item label="报警类型"><dict-tag :options="alarm_type_options" :value="detail.alarmType" /></el-descriptions-item>
        </el-descriptions>
      </div>
      <div style="margin-bottom: 12px;">
        <h4 class="form-header h4">接口 SQL</h4>
        <el-card>
          <div class="prewrap">{{ detail.interfaceSql || '-' }}</div>
        </el-card>
      </div>
      <div>
        <h4 class="form-header h4">字段列表</h4>
        <el-row :gutter="10" class="mb8">
          <el-col :span="1.5">
            <el-button type="primary" plain icon="Plus" @click="openFieldAdd" v-hasPermi="['dataservice:interface-field:add']">新增字段</el-button>
          </el-col>
          <right-toolbar @queryTable="getFieldList" />
        </el-row>
        <el-table v-loading="fieldLoading" :data="fieldList">
          <el-table-column label="参数编码" prop="interfaceParaCode" :show-overflow-tooltip="true" />
          <el-table-column label="参数名称" prop="interfaceParaName" :show-overflow-tooltip="true" />
          <el-table-column label="位置" prop="interfaceParaPosition" width="90" />
          <el-table-column label="类型" prop="interfaceParaType" width="120" />
          <el-table-column label="数据类型" prop="interfaceDataType" width="120" />
          <el-table-column label="默认值" prop="interfaceParaDefault" :show-overflow-tooltip="true" />
          <el-table-column label="显示" prop="interfaceShowFlag" width="90">
            <template #default="scope">
              <dict-tag :options="yes_no_options" :value="scope.row.interfaceShowFlag" />
            </template>
          </el-table-column>
          <el-table-column label="导出" prop="interfaceExportFlag" width="90">
            <template #default="scope">
              <dict-tag :options="yes_no_options" :value="scope.row.interfaceExportFlag" />
            </template>
          </el-table-column>
          <el-table-column label="操作" align="center" width="200" fixed="right">
            <template #default="scope">
              <el-button link type="primary" icon="Edit" @click="openFieldEdit(scope.row)" v-hasPermi="['dataservice:interface-field:edit']">修改</el-button>
              <el-button link type="danger" icon="Delete" @click="handleFieldDelete(scope.row)" v-hasPermi="['dataservice:interface-field:remove']">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>

    <!-- 字段新增/修改弹窗 -->
    <el-dialog :title="fieldTitle" v-model="fieldOpen" width="700px" append-to-body>
      <el-form ref="fieldFormRef" :model="fieldForm" :rules="fieldRules" label-width="140px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="参数编码" prop="interfaceParaCode">
              <el-input v-model="fieldForm.interfaceParaCode" placeholder="请输入参数编码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="参数名称" prop="interfaceParaName">
              <el-input v-model="fieldForm.interfaceParaName" placeholder="请输入参数名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="参数位置" prop="interfaceParaPosition">
              <el-input-number v-model="fieldForm.interfaceParaPosition" :min="0" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="参数类型" prop="interfaceParaType">
              <el-select v-model="fieldForm.interfaceParaType" placeholder="请选择类型">
                <el-option label="输入参数" value="1" />
                <el-option label="输出参数" value="2" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据类型" prop="interfaceDataType">
              <el-select v-model="fieldForm.interfaceDataType" placeholder="请选择数据类型">
                <el-option label="字符" value="1" />
                <el-option label="整数" value="2" />
                <el-option label="小数" value="3" />
                <el-option label="百分比" value="4" />
                <el-option label="无格式整数" value="5" />
                <el-option label="无格式小数" value="6" />
                <el-option label="无格式百分比" value="7" />
                <el-option label="1位百分比" value="8" />
                <el-option label="1位小数" value="9" />
                <el-option label="年份" value="10" />
                <el-option label="日期" value="11" />
                <el-option label="月份" value="12" />
                <el-option label="单选" value="13" />
                <el-option label="多选" value="14" />
                <el-option label="文本" value="15" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="默认值" prop="interfaceParaDefault">
              <el-input v-model="fieldForm.interfaceParaDefault" placeholder="可选：默认值" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否显示" prop="interfaceShowFlag">
              <el-radio-group v-model="fieldForm.interfaceShowFlag">
                <el-radio v-for="dict in yes_no_options" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否导出" prop="interfaceExportFlag">
              <el-radio-group v-model="fieldForm.interfaceExportFlag">
                <el-radio v-for="dict in yes_no_options" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="显示名称" prop="interfaceShowDesc">
              <el-input v-model="fieldForm.interfaceShowDesc" placeholder="可选：显示名称" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="字段描述" prop="interfaceParaDesc">
              <el-input v-model="fieldForm.interfaceParaDesc" type="textarea" :rows="2" placeholder="可选：描述" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitFieldForm">确 定</el-button>
          <el-button @click="cancelField">取 消</el-button>
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
import { listInterfaceInfo, getInterfaceInfo, addInterfaceInfo, updateInterfaceInfo, delInterfaceInfo, listInterfaceFields, addInterfaceField, updateInterfaceField, delInterfaceField, testInterfaceById, executeInterfaceById, exportInterfaceById } from '@/api/dataservice'
import { listDatasource } from '@/api/datasource'

const { proxy } = getCurrentInstance()
const { sys_normal_disable } = proxy.useDict('sys_normal_disable')

const yes_no_options = [
  { value: '1', label: '是' },
  { value: '0', label: '否' },
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

const detailOpen = ref(false)
const detail = ref({})
const fieldLoading = ref(false)
const fieldList = ref([])
const fieldOpen = ref(false)
const fieldTitle = ref('')
const datasourceOptions = ref([])

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
  { value: 'sqlite', label: 'SQLite' },
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
  fieldRules: {
    interfaceParaCode: [{ required: true, message: '参数编码不能为空', trigger: 'blur' }],
    interfaceParaName: [{ required: true, message: '参数名称不能为空', trigger: 'blur' }],
    interfaceParaPosition: [{ type: 'number', message: '位置需为数字', trigger: 'blur' }],
    interfaceParaType: [{ required: true, message: '参数类型不能为空', trigger: 'change' }],
    interfaceDataType: [{ required: true, message: '数据类型不能为空', trigger: 'change' }],
  }
})

const { form, queryParams, rules, fieldRules } = toRefs(data)

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

function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
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
  proxy.$modal.confirm('是否确认删除编号为"' + idsParam + '"的数据项？').then(function() {
    return delInterfaceInfo(idsParam)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

function openDetail(row) {
  const id = row?.interfaceId
  if (!id) return
  getInterfaceInfo(id).then(res => {
    detail.value = res.data || {}
    detailOpen.value = true
    getFieldList()
  })
}

function getFieldList() {
  fieldLoading.value = true
  listInterfaceFields({ interfaceId: detail.value.interfaceId }).then(res => {
    fieldList.value = res.rows || []
    fieldLoading.value = false
  }).catch(() => {
    fieldLoading.value = false
  })
}

function openFieldAdd() {
  resetFieldForm()
  fieldForm.value.interfaceId = detail.value.interfaceId
  fieldOpen.value = true
  fieldTitle.value = '新增字段'
}

function openFieldEdit(row) {
  resetFieldForm()
  Object.assign(fieldForm.value, row || {})
  fieldOpen.value = true
  fieldTitle.value = '修改字段'
}

function submitFieldForm() {
  proxy.$refs['fieldFormRef'].validate(valid => {
    if (!valid) return
    if (fieldForm.value.fieldId !== undefined) {
      updateInterfaceField(fieldForm.value).then(() => {
        proxy.$modal.msgSuccess('修改成功')
        fieldOpen.value = false
        getFieldList()
      })
    } else {
      addInterfaceField(fieldForm.value).then(() => {
        proxy.$modal.msgSuccess('新增成功')
        fieldOpen.value = false
        getFieldList()
      })
    }
  })
}

function handleFieldDelete(row) {
  const idsParam = row?.fieldId
  proxy.$modal.confirm('是否确认删除字段编号为"' + idsParam + '"的数据项？').then(function() {
    return delInterfaceField(idsParam)
  }).then(() => {
    getFieldList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

const fieldForm = ref({})
function resetFieldForm() {
  fieldForm.value = {
    fieldId: undefined,
    interfaceId: undefined,
    interfaceParaCode: undefined,
    interfaceParaName: undefined,
    interfaceParaPosition: 0,
    interfaceParaType: undefined,
    interfaceDataType: undefined,
    interfaceParaDefault: undefined,
    interfaceShowFlag: '1',
    interfaceExportFlag: '1',
    interfaceShowDesc: undefined,
    interfaceParaDesc: undefined,
  }
  proxy.resetForm('fieldFormRef')
}

function loadDatasourceOptions() {
  listDatasource({ pageNum: 1, pageSize: 100 }).then(res => {
    datasourceOptions.value = res.rows || []
  })
}

function handleTest(row) {
  const id = row?.interfaceId
  if (!id) return
  testInterfaceById(id).then(() => {
    proxy.$modal.msgSuccess('连接成功')
  }).catch(err => {
    proxy.$modal.msgError(err?.msg || '连接失败')
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
    const rows = res.data?.rows || []
    execRows.value = rows
    execColumns.value = rows.length ? Object.keys(rows[0]) : []
  }).catch(err => {
    proxy.$modal.msgError(err?.msg || '执行失败')
  }).finally(() => {
    execLoading.value = false
  })
}

function handleExport(row) {
  const id = row?.interfaceId
  if (!id) return
  let paramsObj = null
  if (execForm.value.paramsJson && execForm.value.paramsJson.trim()) {
    try {
      paramsObj = JSON.parse(execForm.value.paramsJson)
    } catch (e) {
      // 不阻塞导出，使用空参数
      paramsObj = null
    }
  }
  exportInterfaceById(id, { params: paramsObj || {}, pageSize: 1000, offset: 0 }).then(res => {
    const blob = new Blob([res], { type: 'text/csv;charset=utf-8' })
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
    const blob = new Blob([res], { type: 'text/csv;charset=utf-8' })
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