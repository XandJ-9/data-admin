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
      <el-table-column label="主机" prop="host" :show-overflow-tooltip="true" />
      <el-table-column label="端口" prop="port" width="90" align="center" />
      <el-table-column label="数据库" prop="dbName" :show-overflow-tooltip="true" />
      <el-table-column label="用户名" prop="username" width="120" :show-overflow-tooltip="true" />
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
            icon="View"
            @click="handleView(scope.row)"
            v-hasPermi="['system:datasource:query']"
          >查看</el-button>
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
    <el-dialog :title="title" v-model="open" width="600px" append-to-body>
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
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
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
const rules = ref({
  dataSourceName: [
    { required: true, message: '数据源名称不能为空', trigger: 'blur' }
  ],
  dbType: [
    { required: true, message: '数据库类型不能为空', trigger: 'change' }
  ],
  host: [
    { required: true, message: '主机不能为空', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '端口不能为空', trigger: 'blur' }
  ],
  dbName: [
    { required: true, message: '数据库不能为空', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '用户名不能为空', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '密码不能为空', trigger: 'blur' }
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
    dataSourceName: null,
    dbType: 'mysql',
    host: 'localhost',
    port: 3306,
    dbName: null,
    username: null,
    password: null,
    params: '{}',
    status: '0',
    remark: null
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
    form.value = response.data
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

/** 查看按钮操作 */
function handleView(row) {
  proxy.$router.push({
    // name: 'DataSourceDetail',
    name: 'DataSourceView',
    params: { id: row.dataSourceId }
  })
}

/** 删除按钮操作 */
function handleDelete(row) {
  const deleteIds = row.dataSourceId || ids.value.join(',')
  proxy.$modal.confirm('是否确认删除数据源编号为"' + deleteIds + '"的数据项？').then(() => {
    return delDatasource(deleteIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

/** 测试连接 - 按ID */
function handleTest(row) {
  const id = row.dataSourceId
  proxy.$modal.confirm('是否测试连接数据源"' + row.dataSourceName + '"？').then(() => {
    testDatasource(id).then(response => {
      proxy.$modal.msgSuccess(response.msg || '连接成功')
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
  // 设置默认端口
  const portMap = {
    mysql: 3306,
    postgresql: 5432,
    oracle: 1521,
    sqlserver: 1433,
    presto: 8080,
    starrocks: 9030
  }
  if (value !== 'sqlite' && !form.value.port) {
    form.value.port = portMap[value] || 3306
  }
  if (value === 'sqlite') {
    form.value.host = ''
    form.value.port = 0
    form.value.username = ''
    form.value.password = ''
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

getList()
</script>
