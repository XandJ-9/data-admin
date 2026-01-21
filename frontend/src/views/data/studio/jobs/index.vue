<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="作业名称" prop="name">
        <el-input
          v-model="queryParams.name"
          placeholder="请输入任务名称"
          clearable
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="任务类型" prop="type" style="width: 240px;">
        <el-select v-model="queryParams.type" placeholder="请选择任务类型" clearable>
          <el-option
            v-for="dict in taskTypeOptions"
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

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="Plus"
          @click="handleAdd"
        >新增</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="taskList">
      <el-table-column label="任务编号" align="center" prop="taskId" />
      <el-table-column label="任务名称" align="center" prop="taskName" />
      <el-table-column label="任务类型" align="center" prop="taskType">
        <template #default="scope">
          <dict-tag :options="taskTypeOptions" :value="scope.row.taskType" />
        </template>
      </el-table-column>
      <el-table-column label="描述" align="center" prop="description" />
      <el-table-column label="状态" align="center" prop="status">
        <template #default="scope">
           <el-tag :type="scope.row.status === '0' ? 'success' : 'danger'">
              {{ scope.row.status === '0' ? '正常' : '停用' }}
           </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" align="center" prop="createTime" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button
            link
            type="primary"
            icon="Edit"
            @click="handleUpdate(scope.row)"
          >编辑</el-button>
          <el-button
            link
            type="primary"
            icon="Delete"
            @click="handleDelete(scope.row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total>0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

  </div>
</template>

<script setup name="JobList">
import { listTasks, delTask } from "@/api/data/studio";
import { ref, reactive, toRefs, getCurrentInstance } from 'vue';
import { useRouter } from 'vue-router';

const { proxy } = getCurrentInstance();
const router = useRouter();

const taskList = ref([]);
const loading = ref(true);
const showSearch = ref(true);
const total = ref(0);

const taskTypeOptions = [
  { value: 'data_integration', label: '数据采集' },
  { value: 'hive', label: 'Hive计算' },
  { value: 'spark', label: 'Spark计算' },
  { value: 'spark_sql', label: 'SparkSQL计算' },
  { value: 'flink', label: 'Flink计算' },
  { value: 'flink_sql', label: 'FlinkSQL计算' },
  { value: 'python', label: 'Python脚本' },
  { value: 'shell', label: 'Shell脚本' }
];

const data = reactive({
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    name: undefined,
    type: undefined,
    status: undefined
  }
});

const { queryParams } = toRefs(data);

/** 查询列表 */
function getList() {
  loading.value = true;
  listTasks(queryParams.value).then(response => {
    taskList.value = response.rows || [];
    total.value = response.total || 0;
  }).finally(() => {
    loading.value = false;
  });
}

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.pageNum = 1;
  getList();
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm("queryRef");
  handleQuery();
}

/** 新增按钮操作 */
function handleAdd() {
  router.push({ name: 'JobDetail', params: { id: 'new' } });
}

/** 修改按钮操作 */
function handleUpdate(row) {
  router.push({ name: 'JobDetail', params: { id: row.taskId }});
}

/** 删除按钮操作 */
function handleDelete(row) {
  const taskId = row.taskId;
  proxy.$modal.confirm('是否确认删除任务【' + row.taskName + '】？').then(function() {
    return delTask(taskId);
  }).then(() => {
    getList();
    proxy.$modal.msgSuccess("删除成功");
  }).catch(() => {});
}

getList();
</script>
