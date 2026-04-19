<template>
  <div class="app-container">
    <!-- 搜索表单 -->
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="数据源名称" prop="dataSourceName">
        <el-input
          v-model="queryParams.dataSourceName"
          placeholder="请输入数据源名称"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="数据库类型" prop="dbType">
        <el-select v-model="queryParams.dbType" placeholder="请选择数据库类型" clearable style="width: 200px">
          <el-option label="MySQL" value="mysql" />
          <el-option label="PostgreSQL" value="postgresql" />
          <el-option label="SQLite" value="sqlite" />
          <el-option label="Oracle" value="oracle" />
          <el-option label="SQL Server" value="sqlserver" />
          <el-option label="Presto" value="presto" />
          <el-option label="StarRocks" value="starrocks" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="请选择状态" clearable style="width: 200px">
          <el-option
            v-for="dict in sys_normal_disable"
            :key="dict.value"
            :label="dict.label"
            :value="dict.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 表格工具栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="Plus"
          @click="handleAdd"
          v-hasPermi="['system:datasource:add']"
        >新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="success"
          plain
          icon="Edit"
          :disabled="single"
          @click="handleUpdate"
          v-hasPermi="['system:datasource:edit']"
        >修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="Delete"
          :disabled="multiple"
          @click="handleDelete"
          v-hasPermi="['system:datasource:remove']"
        >删除</el-button>
      </el-col>
      <right-toolbar
        v-model:showSearch="showSearch"
        @queryTable="getList"
      ></right-toolbar>
    </el-row>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="dataList"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="数据源名称" prop="dataSourceName" :show-overflow-tooltip="true" />
      <el-table-column label="数据库类型" prop="dbType" width="120" align="center">
        <template #default="scope">
          <el-tag :type="getDbTypeTag(scope.row.dbType)">{{ scope.row.dbType }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="数据库" prop="dbName" :show-overflow-tooltip="true" />
      <el-table-column label="连通性" min-width="140">
        <template #default="scope">
          <el-tooltip placement="top" effect="dark">
            <template #content>
              <div class="connectivity-tooltip">
                <div class="connectivity-tooltip-title">{{ getConnectivityLabel(scope.row.connectivityStatus) }}</div>
                <div class="connectivity-tooltip-item">最近测试：{{ getConnectivityTime(scope.row) }}</div>
                <div class="connectivity-tooltip-item">结果说明：{{ getConnectivityMessage(scope.row) }}</div>
              </div>
            </template>
            <div class="connectivity-trigger">
              <el-tag :type="getConnectivityTag(scope.row.connectivityStatus)">
                {{ getConnectivityLabel(scope.row.connectivityStatus) }}
              </el-tag>
              <span class="connectivity-hint">详情</span>
            </div>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="状态" prop="status" width="80" align="center">
        <template #default="scope">
          <el-tag :type="scope.row.status === '0' ? 'success' : 'danger'">
            {{ scope.row.status === '0' ? '正常' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="createTime" width="180" align="center" />
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width" width="280"
      v-hasPermi="['system:datasource:edit','system:datasource:query']"
      >
        <template #default="scope">
          <el-button
            link
            type="primary"
            icon="Connection"
            @click="handleTest(scope.row)"
            v-hasPermi="['system:datasource:edit']"
          >测试</el-button>
          <el-button
            link
            type="primary"
            icon="Edit"
            @click="handleUpdate(scope.row)"
            v-hasPermi="['system:datasource:edit']"
          >修改</el-button>
          <el-button
            link
            type="primary"
            icon="Delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['system:datasource:remove']"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 添加/修改对话框 -->
    <el-dialog :title="title" v-model="open" width="min(600px, 90vw)" append-to-body>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="数据源名称" prop="dataSourceName">
          <el-input v-model="form.dataSourceName" placeholder="请输入数据源名称" maxlength="64" />
        </el-form-item>
        <el-form-item label="数据库类型" prop="dbType">
          <el-select v-model="form.dbType" placeholder="请选择数据库类型" @change="handleDbTypeChange">
            <el-option label="MySQL" value="mysql" />
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="SQLite" value="sqlite" />
            <el-option label="Oracle" value="oracle" />
            <el-option label="SQL Server" value="sqlserver" />
            <el-option label="Presto" value="presto" />
            <el-option label="StarRocks" value="starrocks" />
          </el-select>
        </el-form-item>
        <el-form-item label="主机" prop="host" v-if="form.dbType !== 'sqlite'">
          <el-input v-model="form.host" placeholder="请输入主机地址" />
        </el-form-item>
        <el-form-item label="端口" prop="port" v-if="form.dbType !== 'sqlite'">
          <el-input-number v-model="form.port" :min="0" :max="65535" controls-position="right" style="width: 200px" />
        </el-form-item>
        <el-form-item label="数据库" prop="dbName">
          <el-input v-model="form.dbName" placeholder="请输入数据库名或文件路径" />
        </el-form-item>
        <el-form-item label="用户名" prop="username" v-if="form.dbType !== 'sqlite'">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="form.dbType !== 'sqlite'">
          <el-input v-model="form.password" type="password" :placeholder="form.dataSourceId ? '留空则不修改密码' : '请输入密码'" show-password />
        </el-form-item>
        <el-form-item label="连接参数" prop="params">
          <el-input v-model="form.params" type="textarea" placeholder='请输入连接参数，格式：{"key":"value"}' />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="0">正常</el-radio>
            <el-radio label="1">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancel">取消</el-button>
          <el-button @click="handleTestByBody" :loading="testLoading">测试连接</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="DataSource">
import {
  listDatasource,
  getDatasource,
  addDatasource,
  updateDatasource,
  delDatasource,
  testDatasource,
  testDatasourceByBody
} from '@/api/data/datasource'

const { proxy } = getCurrentInstance()
const { sys_normal_disable } = proxy.useDict('sys_normal_disable')

const dataList = ref([])
const open = ref(false)
const showSearch = ref(true)
const title = ref('')
const loading = ref(false)
const testLoading = ref(false)
const total = ref(0)
const single = ref(true)
const multiple = ref(true)
const ids = ref([])

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  dataSourceName: null,
  dbType: null,
  status: null
})

const form = ref({})

/** 验证连接参数是否为有效的JSON格式 */
function validateParamsJson(rule, value, callback) {
  if (!value) {
    callback()
    return
  }
  try {
    JSON.parse(value)
    callback()
  } catch (e) {
    callback(new Error('连接参数格式错误，请输入有效的JSON格式'))
  }
}

/** 条件验证：非SQLite时必填 */
function validateRequiredIfNotSqlite(rule, value, callback) {
  if (form.value.dbType !== 'sqlite' && !value) {
    callback(new Error(rule.message || '此项不能为空'))
  } else {
    callback()
  }
}

/** 条件验证：非SQLite且新增时必填，编辑时允许为空 */
function validatePasswordRequired(rule, value, callback) {
  if (form.value.dbType !== 'sqlite' && !form.value.dataSourceId && !value) {
    callback(new Error('密码不能为空'))
  } else {
    callback()
  }
}

const rules = ref({
  dataSourceName: [
    { required: true, message: '数据源名称不能为空', trigger: 'blur' }
  ],
  dbType: [
    { required: true, message: '数据库类型不能为空', trigger: 'change' }
  ],
  host: [
    { validator: validateRequiredIfNotSqlite, trigger: 'blur', message: '主机不能为空' }
  ],
  port: [
    { validator: validateRequiredIfNotSqlite, trigger: 'blur', message: '端口不能为空' }
  ],
  dbName: [
    { required: true, message: '数据库不能为空', trigger: 'blur' }
  ],
  username: [
    { validator: validateRequiredIfNotSqlite, trigger: 'blur', message: '用户名不能为空' }
  ],
  password: [
    { validator: validatePasswordRequired, trigger: 'blur' }
  ],
  params: [
    { validator: validateParamsJson, trigger: 'blur' }
  ]
})

/** 查询数据源列表 */
function getList() {
  loading.value = true
  listDatasource(queryParams.value).then(response => {
    dataList.value = response.rows
    total.value = response.total
    loading.value = false
  })
}

/** 取消按钮 */
function cancel() {
  open.value = false
  reset()
}

/** 表单重置 */
function reset() {
  form.value = {
    dataSourceId: null,
    dataSourceName: '',
    dbType: 'mysql',
    host: 'localhost',
    port: 3306,
    dbName: '',
    username: '',
    password: '',
    params: '{}',
    status: '0',
    remark: ''
  }
  proxy.resetForm('formRef')
}

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.dataSourceId)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

/** 新增按钮操作 */
function handleAdd() {
  reset()
  open.value = true
  title.value = '添加数据源'
}

/** 修改按钮操作 */
function handleUpdate(row) {
  reset()
  const id = row.dataSourceId || ids.value[0]
  getDatasource(id).then(response => {
    form.value = {
      ...response.data,
      // 编辑时不回填密码，留空表示不修改
      password: ''
    }
    open.value = true
    title.value = '修改数据源'
  })
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs.formRef.validate(valid => {
    if (valid) {
      if (form.value.dataSourceId) {
        updateDatasource(form.value).then(response => {
          proxy.$modal.msgSuccess('修改成功')
          open.value = false
          getList()
        })
      } else {
        addDatasource(form.value).then(response => {
          proxy.$modal.msgSuccess('新增成功')
          open.value = false
          getList()
        })
      }
    }
  })
}

/** 删除按钮操作 */
function handleDelete(row) {
  const deleteIds = row.dataSourceId || ids.value.join(',')
  let deleteName
  if (row.dataSourceName) {
    deleteName = row.dataSourceName
  } else {
    const selectedNames = dataList.value
      .filter(item => ids.value.includes(item.dataSourceId))
      .map(item => item.dataSourceName)
    deleteName = selectedNames.join('、') || `编号 ${deleteIds}`
  }
  proxy.$modal.confirm('是否确认删除数据源"' + deleteName + '"？删除后不可恢复。').then(() => {
    return delDatasource(deleteIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch((err) => {
    // 仅当非用户取消操作时提示（错误对象有 __handled 标记已由拦截器显示）
    if (err && err !== 'cancel' && !err.__handled) {
      proxy.$modal.msgError(err.message || '删除失败')
    }
  })
}

/** 测试连接 - 按ID */
function handleTest(row) {
  const id = row.dataSourceId
  proxy.$modal.confirm('是否测试连接数据源"' + row.dataSourceName + '"？').then(() => {
    testDatasource(id).then(response => {
      proxy.$modal.msgSuccess(response.msg || '连接成功')
    }).catch(() => {}).finally(() => {
      getList()
    })
  }).catch(() => {})
}

/** 测试连接 - 按请求体 */
function handleTestByBody() {
  proxy.$refs.formRef.validate(valid => {
    if (valid) {
      testLoading.value = true
      testDatasourceByBody(form.value).then(response => {
        proxy.$modal.msgSuccess(response.msg || '连接成功')
      }).finally(() => {
        testLoading.value = false
      })
    }
  })
}

/** 数据库类型变化 */
function handleDbTypeChange(value) {
  const portMap = {
    mysql: 3306,
    postgresql: 5432,
    oracle: 1521,
    sqlserver: 1433,
    presto: 8080,
    starrocks: 9030
  }
  if (value === 'sqlite') {
    // 保存当前连接信息，切回时恢复
    form.value._savedConn = {
      host: form.value.host,
      port: form.value.port,
      username: form.value.username,
      password: form.value.password
    }
    form.value.host = ''
    form.value.port = 0
    form.value.username = ''
    form.value.password = ''
  } else if (form.value._savedConn) {
    // 从 SQLite 切回，恢复之前保存的连接信息
    form.value.host = form.value._savedConn.host || 'localhost'
    form.value.username = form.value._savedConn.username || ''
    form.value.password = form.value._savedConn.password || ''
    form.value.port = portMap[value] || 3306
    form.value._savedConn = null
  } else {
    form.value.port = portMap[value] || 3306
  }
}

/** 获取数据库类型标签颜色 */
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
  return tagMap[dbType] || ''
}

function getConnectivityTag(status) {
  const tagMap = {
    success: 'success',
    failed: 'danger',
    unknown: 'info'
  }
  return tagMap[status] || 'info'
}

function getConnectivityLabel(status) {
  const labelMap = {
    success: '已连通',
    failed: '异常',
    unknown: '未测试'
  }
  return labelMap[status] || '未测试'
}

function getConnectivityTime(row) {
  return row.connectivityTestedAt || '尚未测试或配置已变更'
}

function getConnectivityMessage(row) {
  if (row.connectivityMessage) {
    return row.connectivityMessage
  }
  return row.connectivityStatus === 'unknown' ? '尚未测试或配置已变更' : '连接成功'
}

getList()
</script>

<style scoped>
.connectivity-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.connectivity-hint {
  font-size: 12px;
  color: var(--el-color-primary);
}

.connectivity-tooltip {
  max-width: 320px;
  line-height: 1.5;
}

.connectivity-tooltip-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.connectivity-tooltip-item {
  font-size: 12px;
}
</style>
