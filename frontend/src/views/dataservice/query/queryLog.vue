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
      <el-table-column prop="sqlText" label="SQL" min-width="200">
        <template #default="scope">
          <div v-if="scope.row.sqlText">
            <div v-if="scope.row.sqlText.length <= 100" class="prewrap">
              {{ scope.row.sqlText }}
            </div>
            <div v-else>
              <div class="prewrap">{{ scope.row.sqlText.substring(0, 100) }}...</div>
              <el-button link type="primary" @click="showSqlDetail(scope.row.sqlText)">查看详情</el-button>
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
      <div class="sql-detail">{{ currentSql }}</div>
      <template #footer>
        <el-button @click="sqlDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { listQueryLog } from '@/api/dataservice'
const list = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 10, userName: '', status: '' })

const sqlDetailVisible = ref(false)
const currentSql = ref('')

function showSqlDetail(sql) {
  currentSql.value = sql
  sqlDetailVisible.value = true
}

function getList() {
  query.pageNum = 1
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
.prewrap {
  /* white-space: pre-wrap; */
  word-break: break-word;
  max-width: 600px;
  overflow-x: hidden;
}
.sql-detail {
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 500px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}
</style>
