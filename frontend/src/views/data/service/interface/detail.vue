<template>
  <div class="app-container">
    <div style="margin-bottom: 12px;">
      <el-button icon="ArrowLeft" @click="handleBack">返回</el-button>
      <el-button type="warning" icon="Download" @click="handleExportMeta" v-hasPermi="['dataservice:interface:export']">导出接口定义</el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="接口定义" name="definition">
        <div style="margin-bottom: 12px;">
          <el-descriptions title="基本信息" :column="2" border>
            <el-descriptions-item label="接口名称">{{ detail.interfaceName }}</el-descriptions-item>
            <el-descriptions-item label="接口编码">{{ detail.interfaceCode }}</el-descriptions-item>
            <el-descriptions-item label="负责人">{{ detail.userName || '-' }}</el-descriptions-item>
            <el-descriptions-item label="数据库类型">{{ detail.interfaceDbType }}</el-descriptions-item>
            <el-descriptions-item label="数据库名称">{{ detail.interfaceDbName }}</el-descriptions-item>
            <el-descriptions-item label="业务平台">{{ detail.platformName }}</el-descriptions-item>
            <el-descriptions-item label="模块名称">{{ detail.moduleName }}</el-descriptions-item>
            <el-descriptions-item label="分页">
              <dict-tag :options="yes_no_options" :value="detail.isPaging" />
            </el-descriptions-item>
            <el-descriptions-item label="日期查询">
              <dict-tag :options="yes_no_options" :value="detail.isDateOption" />
            </el-descriptions-item>
            <el-descriptions-item label="合计">
              <dict-tag :options="yes_no_options" :value="detail.isTotal" />
            </el-descriptions-item>
            <el-descriptions-item label="登录验证">
              <dict-tag :options="yes_no_options" :value="detail.isLoginVisit" />
            </el-descriptions-item>
            <el-descriptions-item label="报警类型">
              <dict-tag :options="alarm_type_options" :value="detail.alarmType" />
            </el-descriptions-item>
            <el-descriptions-item label="接口状态">
              <dict-tag :options="enable_options" :value="detail.enable" />
            </el-descriptions-item>
            <el-descriptions-item label="接口SQL">
              <el-button type="primary" link @click="openSql">查看SQL</el-button>
            </el-descriptions-item>
            <el-descriptions-item label="合计SQL">
              <el-button v-if="detail.isTotal === '1' && detail.totalSql" type="primary" link @click="openTotalSql">查看SQL</el-button>
              <span v-else>-</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div>
          <h4 class="form-header h4">字段列表</h4>
          <el-row :gutter="10" class="mb8">
            <el-col :span="1.5">
              <el-button type="primary" plain icon="Plus" @click="openFieldAdd" v-hasPermi="['dataservice:interface-field:add']">新增字段</el-button>
            </el-col>
            <right-toolbar @queryTable="getFieldList" />
          </el-row>

          <h5 style="margin: 10px 0; font-weight: bold;">请求参数</h5>
          <el-table v-loading="fieldLoading" :data="inputFieldList">
            <el-table-column label="参数编码" prop="interfaceParaCode" :show-overflow-tooltip="true" />
            <el-table-column label="参数名称" prop="interfaceParaName" :show-overflow-tooltip="true" />
            <el-table-column label="参数位置" prop="interfaceParaPosition" width="90" />
            <el-table-column label="参数类型" width="120">
              <template #default="scope">
                {{ scope.row.interfaceParaType === '1' ? '输入参数' : '输出参数' }}
              </template>
            </el-table-column>
            <el-table-column label="数据类型" width="120">
              <template #default="scope">
                {{ dataTypeMap[scope.row.interfaceDataType] || scope.row.interfaceDataType }}
              </template>
            </el-table-column>
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

          <h5 style="margin: 20px 0 10px 0; font-weight: bold;">响应参数</h5>
          <el-table v-loading="fieldLoading" :data="displayOutputFieldList" border :cell-style="() => {}">
            <el-table-column label="参数编码" prop="interfaceParaCode" :show-overflow-tooltip="true" />
            <el-table-column label="参数名称" prop="interfaceParaName" :show-overflow-tooltip="true" />
            <el-table-column label="参数位置" prop="interfaceParaPosition" width="90" />
            <el-table-column label="参数类型" width="120">
              <template #default="scope">
                {{ scope.row.interfaceParaType === '1' ? '输入参数' : '输出参数' }}
              </template>
            </el-table-column>
            <el-table-column label="数据类型" width="120">
              <template #default="scope">
                {{ dataTypeMap[scope.row.interfaceDataType] || scope.row.interfaceDataType }}
              </template>
            </el-table-column>
            <el-table-column label="字段描述" prop="interfaceParaDesc" width="120" />
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
            <el-table-column label="父级表头名称" prop="interfaceParentName" width="120" />
            <el-table-column label="父级表头位置" prop="interfaceParentPosition" width="120" />
            <el-table-column label="是否合并" prop="interfaceParaRowspan" width="120">
              <template #default="scope">
                <dict-tag :options="yes_no_options" :value="scope.row.interfaceParaRowspan" />
              </template>
            </el-table-column>
            <el-table-column label="是否显示备注" prop="interfaceShowDesc" width="120">
              <template #default="scope">
                <dict-tag :options="yes_no_options" :value="scope.row.interfaceShowDesc" />
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

        <pagination
          v-show="outputFieldList.length > 0"
          :total="outputFieldList.length"
          :page="pageNum"
          :limit="pageSize"
          :autoScroll="false"
          @update:page="val => (pageNum = val)"
          @update:limit="val => (pageSize = val)"
        />
      </el-tab-pane>

      <el-tab-pane label="接口测试" name="test">
        <el-card shadow="never" class="mb12">
          <template #header>测试输入</template>
          <el-form label-width="120px">
            <el-form-item label="参数(JSON)">
              <el-input v-model="testForm.paramsJson" type="textarea" :rows="5" placeholder='例如: {&#10;  "startDate": "2024-01-01",&#10;  "endDate": "2024-12-31"&#10;}' />
            </el-form-item>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="返回条数">
                  <el-input-number v-model="testForm.pageSize" :min="1" :max="100" controls-position="right" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="偏移量">
                  <el-input-number v-model="testForm.offset" :min="0" controls-position="right" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item>
              <el-button type="primary" :loading="testLoading" @click="runTest" v-hasPermi="['dataservice:interface:execute']">执行测试</el-button>
              <span class="test-hint">按真实接口调用协议执行，并展示接口原始响应报文。</span>
            </el-form-item>
          </el-form>
        </el-card>

        <el-row :gutter="16" class="mb12">
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>返回结构说明</template>
              <el-table :data="responseSchemaList" max-height="420">
                <el-table-column label="字段编码" prop="interfaceParaCode" min-width="140" :show-overflow-tooltip="true" />
                <el-table-column label="字段名称" prop="interfaceParaName" min-width="140" :show-overflow-tooltip="true" />
                <el-table-column label="数据类型" min-width="110">
                  <template #default="scope">
                    {{ dataTypeMap[scope.row.interfaceDataType] || scope.row.interfaceDataType }}
                  </template>
                </el-table-column>
                <el-table-column label="字段描述" min-width="160" :show-overflow-tooltip="true">
                  <template #default="scope">
                    {{ scope.row.interfaceParaDesc || '-' }}
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never" class="response-card">
              <template #header>
                <div class="response-card-header">
                  <span>真实响应报文</span>
                  <el-button text type="primary" :disabled="!hasTestResponse" @click="copyResponseJson">
                    {{ responsePreviewTab === 'payload' ? '复制原始报文' : '复制 data 载荷' }}
                  </el-button>
                </div>
              </template>
              <template v-if="hasTestResponse">
                <div class="response-summary">
                  <div class="response-summary-item">
                    <span class="summary-label">状态码</span>
                    <strong>{{ testResponseSummary.code }}</strong>
                  </div>
                  <div class="response-summary-item">
                    <span class="summary-label">响应消息</span>
                    <strong>{{ testResponseSummary.msg }}</strong>
                  </div>
                  <div class="response-summary-item">
                    <span class="summary-label">返回记录</span>
                    <strong>{{ testResponseSummary.rowCount }}</strong>
                  </div>
                  <div class="response-summary-item">
                    <span class="summary-label">字段数量</span>
                    <strong>{{ testResponseSummary.columnCount }}</strong>
                  </div>
                </div>
                <el-tabs v-model="responsePreviewTab" class="response-tabs">
                  <el-tab-pane label="原始报文" name="payload">
                    <VAceEditor
                      :value="testResultJson"
                      lang="json"
                      theme="xcode"
                      :options="jsonAceOptions"
                      style="height: 320px; border: 1px solid #dcdfe6; border-radius: 6px;"
                    />
                  </el-tab-pane>
                  <el-tab-pane label="data载荷" name="data">
                    <VAceEditor
                      :value="testDataJson"
                      lang="json"
                      theme="xcode"
                      :options="jsonAceOptions"
                      style="height: 320px; border: 1px solid #dcdfe6; border-radius: 6px;"
                    />
                  </el-tab-pane>
                </el-tabs>
              </template>
              <el-empty v-else description="执行一次测试后，可查看真实响应报文" :image-size="72" />
            </el-card>
          </el-col>
        </el-row>

        <el-card shadow="never">
          <template #header>测试结果预览</template>
          <el-table v-loading="testLoading" :data="testRows" max-height="360">
            <el-table-column v-for="col in testColumns" :key="col" :prop="col" :label="col" min-width="140" :show-overflow-tooltip="true" />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="sqlOpen" title="查看SQL" width="800px" append-to-body>
      <VAceEditor
        v-model:value="detail.interfaceSql"
        lang="sql"
        theme="xcode"
        :options="aceOptions"
        style="height: 400px; border: 1px solid #ccc;"
        readonly
      />
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="sqlOpen = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="totalSqlOpen" title="查看合计SQL" width="800px" append-to-body>
      <VAceEditor
        v-model:value="detail.totalSql"
        lang="sql"
        theme="xcode"
        :options="aceOptions"
        style="height: 400px; border: 1px solid #ccc;"
        readonly
      />
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="totalSqlOpen = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>

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
  </div>
</template>

<script setup name="InterfaceDetail">
import { getInterfaceInfo, listInterfaceFields, addInterfaceField, updateInterfaceField, delInterfaceField, executeInterfaceById } from '@/api/data/service'
import { useRoute, useRouter } from 'vue-router'
import { VAceEditor } from 'vue3-ace-editor'
import 'ace-builds/src-noconflict/ext-language_tools'
import 'ace-builds/src-noconflict/mode-sql'
import 'ace-builds/src-noconflict/mode-json'
import 'ace-builds/src-noconflict/snippets/sql'
import 'ace-builds/src-noconflict/theme-xcode'

const { proxy } = getCurrentInstance()
const route = useRoute()
const router = useRouter()

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

const detail = ref({})
const fieldLoading = ref(false)
const fieldList = ref([])
const fieldOpen = ref(false)
const activeTab = ref(route.query.tab === 'test' ? 'test' : 'definition')
const testLoading = ref(false)
const testForm = ref({ paramsJson: undefined, pageSize: 10, offset: 0 })
const testColumns = ref([])
const testRows = ref([])
const testResponsePayload = ref(null)
const responsePreviewTab = ref('payload')

const dataTypeMap = {
  '1': '字符',
  '2': '整数',
  '3': '小数',
  '4': '百分比',
  '5': '无格式整数',
  '6': '无格式小数',
  '7': '无格式百分比',
  '8': '1位百分比',
  '9': '1位小数',
  '10': '年份',
  '11': '日期',
  '12': '月份',
  '13': '单选',
  '14': '多选',
  '15': '文本',
}

const inputFieldList = computed(() => {
  return (fieldList.value || [])
    .filter(item => item.interfaceParaType === '1')
    .sort((a, b) => (a.interfaceParaPosition || 0) - (b.interfaceParaPosition || 0))
})

const pageSize = ref(20)
const pageNum = ref(1)

const outputFieldList = computed(() => {
  return (fieldList.value || [])
    .filter(item => item.interfaceParaType === '2')
    .sort((a, b) => (a.interfaceParaPosition || 0) - (b.interfaceParaPosition || 0))
})

const displayOutputFieldList = computed(() => {
  return outputFieldList.value.slice(pageSize.value * (pageNum.value - 1), pageSize.value * pageNum.value)
})

const responseSchemaList = computed(() => outputFieldList.value)
const hasTestResponse = computed(() => Boolean(testResponsePayload.value))
const testResponseSummary = computed(() => ({
  code: testResponsePayload.value?.code ?? '-',
  msg: testResponsePayload.value?.msg || '-',
  rowCount: testRows.value.length,
  columnCount: testColumns.value.length,
}))
const testResultJson = computed(() => JSON.stringify(testResponsePayload.value || {
  code: 200,
  msg: '操作成功',
  data: {
    columns: [],
    rows: [],
  },
}, null, 2))
const testDataJson = computed(() => JSON.stringify(testResponsePayload.value?.data || {
  columns: [],
  rows: [],
}, null, 2))

const fieldTitle = ref('')
const sqlOpen = ref(false)
const totalSqlOpen = ref(false)
const aceOptions = {
  fontSize: 14,
  showPrintMargin: false,
  wrap: true,
  enableBasicAutocompletion: true,
  enableLiveAutocompletion: true,
  enableSnippets: true,
  readOnly: true,
}

const jsonAceOptions = {
  ...aceOptions,
  showLineNumbers: true,
  showGutter: true,
  highlightActiveLine: false,
}

const data = reactive({
  fieldRules: {
    interfaceParaCode: [{ required: true, message: '参数编码不能为空', trigger: 'blur' }],
    interfaceParaName: [{ required: true, message: '参数名称不能为空', trigger: 'blur' }],
    interfaceParaPosition: [{ type: 'number', message: '位置需为数字', trigger: 'blur' }],
    interfaceParaType: [{ required: true, message: '参数类型不能为空', trigger: 'change' }],
    interfaceDataType: [{ required: true, message: '数据类型不能为空', trigger: 'change' }],
  },
})

const { fieldRules } = toRefs(data)

function getDetail() {
  const id = route.params.interfaceId
  if (!id) return
  getInterfaceInfo(id).then(res => {
    detail.value = res.data || {}
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

function openSql() {
  sqlOpen.value = true
}

function openTotalSql() {
  totalSqlOpen.value = true
}

function handleTabChange(tabName) {
  const query = tabName === 'test' ? { tab: 'test' } : {}
  router.replace({ name: 'InterfaceDetail', params: { interfaceId: route.params.interfaceId }, query })
}

async function copyResponseJson() {
  const copyText = responsePreviewTab.value === 'data' ? testDataJson.value : testResultJson.value
  try {
    await navigator.clipboard.writeText(copyText)
    proxy.$modal.msgSuccess('复制成功')
  } catch (error) {
    proxy.$modal.msgError('复制失败，请手动复制')
  }
}

function runTest() {
  const id = detail.value.interfaceId
  if (!id) return
  let paramsObj = null
  if (testForm.value.paramsJson && testForm.value.paramsJson.trim()) {
    try {
      paramsObj = JSON.parse(testForm.value.paramsJson)
    } catch (e) {
      proxy.$modal.msgError('参数JSON格式错误')
      return
    }
  }
  testLoading.value = true
  testColumns.value = []
  testRows.value = []
  testResponsePayload.value = null
  executeInterfaceById(id, {
    params: paramsObj || {},
    pageSize: testForm.value.pageSize,
    offset: testForm.value.offset,
  }).then(res => {
    const records = Array.isArray(res.data) ? res.data : (res.data?.list || [])
    const outputColumns = outputFieldList.value
      .map(item => item.interfaceParaCode)
      .filter(Boolean)
    testColumns.value = outputColumns.length ? outputColumns : Object.keys(records[0] || {})
    testRows.value = records.map(item => {
      if (item && typeof item === 'object' && !Array.isArray(item)) {
        return item
      }
      const rowObj = {}
      testColumns.value.forEach((col, index) => {
        rowObj[col] = Array.isArray(item) ? item[index] : undefined
      })
      return rowObj
    })
    testResponsePayload.value = res
  }).catch(err => {
    proxy.$modal.msgError(err?.msg || '测试失败')
  }).finally(() => {
    testLoading.value = false
  })
}

function handleBack() {
  router.push({ name: 'DataServiceInterface' })
}

function handleExportMeta() {
  const id = detail.value.interfaceId
  if (!id) return
  proxy.download('/dataservice/interface-info/' + id + '/export-meta', {}, `interface_${id}_meta.xlsx`)
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
  proxy.$refs.fieldFormRef.validate(valid => {
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

function cancelField() {
  fieldOpen.value = false
  resetFieldForm()
}

watch(() => route.query.tab, value => {
  activeTab.value = value === 'test' ? 'test' : 'definition'
})

getDetail()
</script>

<style scoped>
.mb8 { margin-bottom: 8px; }
.mb12 { margin-bottom: 12px; }
.test-hint { margin-left: 12px; color: var(--el-text-color-secondary); }
.prewrap { white-space: pre-wrap; word-break: break-word; }
.response-card-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.response-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 12px; }
.response-summary-item { padding: 12px; border: 1px solid var(--el-border-color-light); border-radius: 6px; background: var(--el-fill-color-lighter); }
.summary-label { display: block; margin-bottom: 6px; color: var(--el-text-color-secondary); font-size: 12px; }
.response-tabs :deep(.el-tabs__content) { padding-top: 4px; }
</style>
