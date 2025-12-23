<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="任务ID" prop="task">
        <el-input
          v-model="queryParams.task"
          placeholder="请输入任务ID"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="任务名称" prop="task__task_name">
        <el-input
          v-model="queryParams.task__task_name"
          placeholder="请输入任务名称"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="请选择状态" clearable style="width: 240px">
          <el-option label="运行中" value="running" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
        <el-button icon="Back" @click="handleBack">返回</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="logList">
      <el-table-column label="日志编号" align="center" prop="id" />
      <el-table-column label="任务名称" align="center" prop="task_name" />
      <el-table-column label="状态" align="center" prop="status">
        <template #default="scope">
            <el-tag v-if="scope.row.status === 'success'" type="success">成功</el-tag>
            <el-tag v-else-if="scope.row.status === 'failed'" type="danger">失败</el-tag>
            <el-tag v-else type="primary">运行中</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="开始时间" align="center" prop="start_time" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.start_time) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="结束时间" align="center" prop="end_time" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.end_time) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="日志信息" align="center" prop="message" :show-overflow-tooltip="true" />
    </el-table>

    <pagination
      v-show="total>0"
      :total="total"
      v-model:page="queryParams.page"
      v-model:limit="queryParams.page_size"
      @pagination="getList"
    />
  </div>
</template>

<script setup name="TaskLog">
import { listTaskLog } from "@/api/datataskmonitor";
import { parseTime } from "@/utils/ruoyi";
import { useRoute, useRouter } from 'vue-router';

const { proxy } = getCurrentInstance();
const route = useRoute();
const router = useRouter();

const logList = ref([]);
const loading = ref(true);
const showSearch = ref(true);
const total = ref(0);

const queryParams = ref({
  page: 1,
  page_size: 10,
  task: undefined,
  task__task_name: undefined,
  status: undefined
});

/** 查询日志列表 */
function getList() {
  loading.value = true;
  listTaskLog(queryParams.value).then(response => {
    logList.value = response.results;
    total.value = response.count;
    loading.value = false;
  });
}

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.page = 1;
  getList();
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm("queryRef");
  handleQuery();
}

/** 返回按钮 */
function handleBack() {
    router.push('/datataskmonitor/index');
}

// Init
if (route.query.taskId) {
    queryParams.value.task = route.query.taskId;
}
getList();
</script>
