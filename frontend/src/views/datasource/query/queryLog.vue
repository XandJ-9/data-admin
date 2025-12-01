<template>
  <div class="app-container">
    <el-form :inline="true" label-width="80px" style="margin-bottom: 12px">
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
    <el-table :data="list" border>
      <el-table-column prop="createTime" label="时间" width="180" />
      <el-table-column prop="userName" label="用户" width="120" />
      <el-table-column prop="dataSourceName" label="数据源" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="durationMs" label="耗时(ms)" width="120" />
      <el-table-column prop="sqlText" label="SQL">
        <template #default="scope">
          <el-tooltip :content="scope.row.sqlText" placement="top">
            <span class="ellipsis">{{ scope.row.sqlText }}</span>
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>
    <pagination v-show="total>0" :total="total" v-model:page="query.pageNum" v-model:limit="query.pageSize" @pagination="getList" />
  </div>
</template>

<script setup>
import { listQueryLog } from '@/api/datasource'
const list = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 10, userName: '', status: '' })

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
</style>
