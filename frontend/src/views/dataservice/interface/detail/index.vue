<template>
  <div class="app-container">
    <div style="margin-bottom: 12px;">
      <el-button icon="ArrowLeft" @click="handleBack">返回</el-button>
      <el-button type="warning" icon="Download" @click="handleExportMeta" v-hasPermi="['dataservice:interface:export']">导出接口定义</el-button>
    </div>

    <div style="margin-bottom: 12px;">
      <el-descriptions title="基本信息" :column="2" border>
        <el-descriptions-item label="接口名称">{{ detail.interfaceName }}</el-descriptions-item>
        <el-descriptions-item label="接口编码">{{ detail.interfaceCode }}</el-descriptions-item>
        <el-descriptions-item label="数据库类型">{{ detail.interfaceDbType }}</el-descriptions-item>
        <el-descriptions-item label="数据库名称">{{ detail.interfaceDbName }}</el-descriptions-item>
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
      </el-descriptions>
    </div>

    <!-- SQL查看弹窗 -->
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
        <el-table-column label="字段描述" prop="interfaceParaDesc" width="120"/>
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
        <el-table-column label="父级表头名称" prop="interfaceParentName" width="120"/>
        <el-table-column label="父级表头位置" prop="interfaceParentPosition" width="120"/>
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
  </div>
</template>

<script setup name="InterfaceDetail">
import { getInterfaceInfo, listInterfaceFields, addInterfaceField, updateInterfaceField, delInterfaceField, exportInterfaceMeta } from '@/api/dataservice'
import { useRoute, useRouter } from 'vue-router'
import { VAceEditor } from 'vue3-ace-editor'
import 'ace-builds/src-noconflict/ext-language_tools'
import 'ace-builds/src-noconflict/mode-sql'
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
    return outputFieldList.value.slice(pageSize.value * (pageNum.value-1), pageSize.value * pageNum.value )

})

const fieldTitle = ref('')

const sqlOpen = ref(false)
const aceOptions = {
  fontSize: 14,
  showPrintMargin: false,
  wrap: true,
  enableBasicAutocompletion: true,
  enableLiveAutocompletion: true,
  enableSnippets: true,
  readOnly: true
}

const data = reactive({
  fieldRules: {
    interfaceParaCode: [{ required: true, message: '参数编码不能为空', trigger: 'blur' }],
    interfaceParaName: [{ required: true, message: '参数名称不能为空', trigger: 'blur' }],
    interfaceParaPosition: [{ type: 'number', message: '位置需为数字', trigger: 'blur' }],
    interfaceParaType: [{ required: true, message: '参数类型不能为空', trigger: 'change' }],
    interfaceDataType: [{ required: true, message: '数据类型不能为空', trigger: 'change' }],
  }
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

function handleBack() {
    //   router.push('/dataservice/dataInterface')
    router.push({name: 'DataInterface'})
}

// 导出元数据
function handleExportMeta() {
  const id = detail.value.interfaceId
  if (!id) return
//   exportInterfaceMeta(id).then(res => {
//     const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
//     const url = window.URL.createObjectURL(blob)
//     const a = document.createElement('a')
//     a.href = url
//     a.download = `interface_${id}_meta.xlsx`
//     document.body.appendChild(a)
//     a.click()
//     document.body.removeChild(a)
//     window.URL.revokeObjectURL(url)
//     proxy.$modal.msgSuccess('导出成功')
//   }).catch(err => {
//     proxy.$modal.msgError(err?.msg || '导出失败')
//   })
    proxy.download('/dataservice/interface-info/' + id + '/export-meta', {},`interface_${id}_meta.xlsx`)
}

// 字段相关
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

function cancelField() {
  fieldOpen.value = false
  resetFieldForm()
}

getDetail()
</script>

<style scoped>
.mb8 { margin-bottom: 8px; }
.prewrap { white-space: pre-wrap; word-break: break-word; }
</style>
