<template>
  <div class="app-container">
    <el-form v-if="showSearch" :model="queryParams" ref="queryRef" :inline="true">
      <el-form-item label="报表名称" prop="reportName">
        <el-input v-model="queryParams.reportName" placeholder="请输入报表名称" clearable style="width: 200px" @keyup.enter="getList" />
      </el-form-item>
      <el-form-item label="报表编码" prop="reportCode">
        <el-input v-model="queryParams.reportCode" placeholder="请输入报表编码" clearable style="width: 200px" @keyup.enter="getList" />
      </el-form-item>
      <el-form-item label="负责人" prop="userName">
        <el-input v-model="queryParams.userName" placeholder="请输入负责人" clearable style="width: 200px" @keyup.enter="getList" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="getList">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['dataservice:report:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['dataservice:report:remove']">删除</el-button>
      </el-col>
      <right-toolbar :showSearch="showSearch" @update:showSearch="val => (showSearch = val)" @queryTable="getList" />
    </el-row>

    <el-table v-loading="loading" :data="dataList" @selection-change="handleSelectionChange" border>
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="报表名称" prop="reportName" min-width="180" :show-overflow-tooltip="true" />
      <el-table-column label="报表编码" prop="reportCode" min-width="180" :show-overflow-tooltip="true" />
      <el-table-column label="负责人" prop="userName" width="140" :show-overflow-tooltip="true" />
      <el-table-column label="接口数量" prop="interfaceCount" width="100" align="center" />
      <el-table-column label="报表描述" prop="reportDesc" min-width="220" :show-overflow-tooltip="true" />
      <el-table-column label="创建时间" align="center" prop="createTime" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="260" fixed="right">
        <template #default="scope">
          <el-button link size="small" type="primary" icon="View" @click="handleDetail(scope.row)">详情</el-button>
          <el-button link size="small" type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['dataservice:report:edit']">修改</el-button>
          <el-button link size="small" type="danger" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['dataservice:report:remove']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      :page="queryParams.pageNum"
      :limit="queryParams.pageSize"
      @update:page="val => (queryParams.pageNum = val)"
      @update:limit="val => (queryParams.pageSize = val)"
      @pagination="getList"
    />

    <el-dialog :title="title" v-model="open" width="760px" append-to-body>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="报表名称" prop="reportName">
              <el-input v-model="form.reportName" placeholder="请输入报表名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="报表编码" prop="reportCode">
              <el-input v-model="form.reportCode" placeholder="请输入报表编码，仅支持字母数字中划线下划线" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负责人" prop="userName">
              <el-input v-model="form.userName" placeholder="默认取当前登录用户" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="报表描述" prop="reportDesc">
              <el-input v-model="form.reportDesc" type="textarea" :rows="3" placeholder="请输入报表描述" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="关联接口" prop="interfaceIds">
              <el-select v-model="form.interfaceIds" multiple filterable collapse-tags collapse-tags-tooltip placeholder="请选择一个或多个接口" style="width: 100%">
                <el-option v-for="item in interfaceOptions" :key="item.interfaceId" :label="`${item.interfaceName}（${item.interfaceCode}）`" :value="item.interfaceId" />
              </el-select>
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

    <el-dialog title="报表详情" v-model="detailOpen" width="900px" append-to-body>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="报表名称">{{ detail.reportName }}</el-descriptions-item>
        <el-descriptions-item label="报表编码">{{ detail.reportCode }}</el-descriptions-item>
        <el-descriptions-item label="负责人">{{ detail.userName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="接口数量">{{ detail.interfaceCount || 0 }}</el-descriptions-item>
        <el-descriptions-item label="报表描述" :span="2">{{ detail.reportDesc || '-' }}</el-descriptions-item>
      </el-descriptions>
      <h4 class="detail-title">关联接口</h4>
      <el-table :data="detail.interfaces || []" border>
        <el-table-column label="接口名称" prop="interfaceName" min-width="180" :show-overflow-tooltip="true" />
        <el-table-column label="接口编码" prop="interfaceCode" min-width="180" :show-overflow-tooltip="true" />
        <el-table-column label="负责人" prop="userName" width="140" :show-overflow-tooltip="true" />
        <el-table-column label="状态" prop="enable" width="90">
          <template #default="scope">
            <dict-tag :options="enableOptions" :value="scope.row.enable" />
          </template>
        </el-table-column>
        <el-table-column label="接口描述" prop="interfaceDesc" min-width="220" :show-overflow-tooltip="true" />
      </el-table>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailOpen = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="DataServiceReport">
import { listReportInfo, getReportInfo, addReportInfo, updateReportInfo, delReportInfo, listInterfaceInfo } from '@/api/data/service'
import useUserStore from '@/store/modules/user'

const { proxy } = getCurrentInstance()
const userStore = useUserStore()

const enableOptions = [
  { value: '1', label: '启用' },
  { value: '0', label: '禁用' },
]

const loading = ref(true)
const showSearch = ref(true)
const ids = ref([])
const multiple = ref(true)
const total = ref(0)
const dataList = ref([])
const open = ref(false)
const detailOpen = ref(false)
const title = ref('')
const interfaceOptions = ref([])
const detail = ref({})

const data = reactive({
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    reportName: undefined,
    reportCode: undefined,
    userName: undefined,
  },
  form: {},
  rules: {
    reportName: [{ required: true, message: '报表名称不能为空', trigger: 'blur' }],
    reportCode: [
      { required: true, message: '报表编码不能为空', trigger: 'blur' },
      { pattern: /^[A-Za-z0-9_-]+$/, message: '报表编码仅支持字母、数字、中划线和下划线', trigger: 'blur' },
    ],
    interfaceIds: [{ required: true, type: 'array', min: 1, message: '请至少选择一个接口', trigger: 'change' }],
  },
})

const { queryParams, form, rules } = toRefs(data)

function reset() {
  form.value = {
    reportId: undefined,
    reportName: undefined,
    reportCode: undefined,
    reportDesc: undefined,
    userName: userStore.name || undefined,
    interfaceIds: [],
  }
  proxy.resetForm('formRef')
}

function getList() {
  loading.value = true
  listReportInfo(queryParams.value).then(res => {
    dataList.value = res.rows || []
    total.value = res.total || 0
    loading.value = false
  }).catch(() => {
    loading.value = false
  })
}

function loadInterfaceOptions() {
  listInterfaceInfo({ pageNum: 1, pageSize: 1000 }).then(res => {
    interfaceOptions.value = res.rows || []
  })
}

function resetQuery() {
  proxy.resetForm('queryRef')
  queryParams.value.pageNum = 1
  getList()
}

function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.reportId)
  multiple.value = selection.length === 0
}

function handleAdd() {
  reset()
  open.value = true
  title.value = '新增报表'
  loadInterfaceOptions()
}

function handleUpdate(row) {
  reset()
  getReportInfo(row.reportId).then(res => {
    form.value = {
      ...res.data,
      interfaceIds: (res.data?.interfaces || []).map(item => item.interfaceId),
    }
    open.value = true
    title.value = '修改报表'
    loadInterfaceOptions()
  })
}

function handleDetail(row) {
  getReportInfo(row.reportId).then(res => {
    detail.value = res.data || {}
    detailOpen.value = true
  })
}

function submitForm() {
  proxy.$refs.formRef.validate(valid => {
    if (!valid) return
    const payload = { ...form.value }
    const request = form.value.reportId ? updateReportInfo(payload) : addReportInfo(payload)
    request.then(() => {
      proxy.$modal.msgSuccess(form.value.reportId ? '修改成功' : '新增成功')
      open.value = false
      getList()
    })
  })
}

function handleDelete(row) {
  const selectedIds = row?.reportId ? [row.reportId] : ids.value
  if (!selectedIds.length) return
  const confirmText = row?.reportId
    ? `是否确认删除报表“${row.reportName}”？`
    : `是否确认删除已选择的 ${selectedIds.length} 个报表？`
  proxy.$modal.confirm(confirmText).then(() => {
    return delReportInfo(selectedIds.join(','))
  }).then(() => {
    proxy.$modal.msgSuccess('删除成功')
    getList()
  }).catch(() => {})
}

function cancel() {
  open.value = false
  reset()
}

loadInterfaceOptions()
getList()
</script>

<style scoped>
.mb8 { margin-bottom: 8px; }
.detail-title { margin: 20px 0 12px; font-size: 16px; font-weight: 600; }
</style>
