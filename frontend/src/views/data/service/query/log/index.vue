<template>
  <div class="app-container">
    <el-form :inline="true">
      <el-form-item label="用户">
        <el-input v-model="query.userName" placeholder="用户名" style="width: 200px" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="query.status" placeholder="全部" style="width: 160px">
          <el-option label="全部" value="" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="fail" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="getList">查询</el-button>
        <el-button @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>
    <el-table :data="list" border style="width: 100%">
      <el-table-column prop="createTime" label="时间" width="180" />
      <el-table-column prop="userName" label="用户" width="120" />
      <el-table-column prop="dataSourceName" label="数据源" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="durationMs" label="耗时(ms)" width="120" />
      <el-table-column prop="queryType" label="查询类型" width="120">
        <template #default="scope">
          <span v-if="scope.row.queryType === 'sql'">SQL查询</span>
          <span v-else-if="scope.row.queryType === 'interface'">接口查询</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="sqlText" label="SQL" min-width="200">
        <template #default="scope">
          <div v-if="scope.row.sqlText" class="sql-cell">
            <code class="sql-preview">{{ scope.row.sqlText }}</code>
            <div class="sql-actions">
              <el-button link type="primary" @click="showSqlDetail(scope.row.sqlText)">
                <el-icon><View /></el-icon>查看
              </el-button>
            </div>
          </div>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="errorMsg" label="错误信息">
        <template #default="scope">
          <el-tooltip :content="scope.row.errorMsg" placement="top" v-if="scope.row.errorMsg">
            <span class="ellipsis">{{ scope.row.errorMsg }}</span>
          </el-tooltip>
          <span v-else>-</span>
        </template>
      </el-table-column>

    </el-table>
    <pagination
      v-show="total>0"
      :total="total"
      :page="query.pageNum"
      :limit="query.pageSize"
      @update:page="val => (query.pageNum = val)"
      @update:limit="val => (query.pageSize = val)"
      @pagination="getList"
    />

    <el-dialog v-model="sqlDetailVisible" title="SQL详情" width="800px">
      <div class="sql-detail-header">
        <el-button type="primary" link v-copyText="currentSql" v-copyText:callback="onCopySuccess">
          <el-icon><DocumentCopy /></el-icon>复制SQL
        </el-button>
      </div>
      <pre class="sql-detail">{{ currentSql }}</pre>
      <template #footer>
        <el-button @click="sqlDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { listQueryLog } from '@/api/data/service'
import { ElMessage } from 'element-plus'

const list = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 10, userName: '', status: '' })

const sqlDetailVisible = ref(false)
const currentSql = ref('')

function showSqlDetail(sql) {
  currentSql.value = sql
  sqlDetailVisible.value = true
}

function onCopySuccess() {
  ElMessage.success('已复制到剪贴板')
}

function getList() {
  listQueryLog(query).then(res => {
    list.value = res.rows || []
    total.value = res.total || 0
  })
}

function resetQuery() {
  query.userName = ''
  query.status = ''
  query.pageNum = 1
  getList()
}

onMounted(() => {
  getList()
})
</script>

<style scoped>
.ellipsis {
  display: inline-block;
  max-width: 600px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sql-cell {
  max-width: 600px;
}
.sql-preview {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12px;
  line-height: 1.5;
  color: #303133;
  background: transparent;
  padding: 0;
}
.sql-actions {
  margin-top: 4px;
  display: flex;
  gap: 8px;
}
.sql-detail-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
.sql-detail {
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 500px;
  overflow-y: auto;
  padding: 16px;
  margin: 0;
  background-color: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, Monaco, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #303133;
}
</style>
