<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="任务名称" prop="task_name">
        <el-input
          v-model="queryParams.task_name"
          placeholder="请输入任务名称"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="任务类型" prop="task_type">
        <el-select v-model="queryParams.task_type" placeholder="请选择任务类型" clearable style="width: 240px">
          <el-option label="数据采集" value="collection" />
          <el-option label="数据同步" value="sync" />
          <el-option label="数据计算" value="calculation" />
          <el-option label="数据存储" value="storage" />
        </el-select>
      </el-form-item>
      <el-form-item label="任务状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="请选择任务状态" clearable style="width: 240px">
          <el-option label="运行中" value="running" />
          <el-option label="暂停" value="paused" />
          <el-option label="失败" value="failed" />
          <el-option label="成功" value="success" />
          <el-option label="空闲" value="idle" />
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
      <el-col :span="1.5">
        <el-button
          type="success"
          plain
          icon="Edit"
          :disabled="single"
          @click="handleUpdate"
        >修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="Delete"
          :disabled="multiple"
          @click="handleDelete"
        >删除</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="taskList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="任务编号" align="center" prop="id" />
      <el-table-column label="任务名称" align="center" prop="task_name" :show-overflow-tooltip="true" />
      <el-table-column label="任务类型" align="center" prop="task_type">
        <template #default="scope">
           <el-tag v-if="scope.row.task_type === 'collection'">数据采集</el-tag>
           <el-tag v-else-if="scope.row.task_type === 'sync'" type="success">数据同步</el-tag>
           <el-tag v-else-if="scope.row.task_type === 'calculation'" type="warning">数据计算</el-tag>
           <el-tag v-else type="info">数据存储</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="调度类型" align="center" prop="schedule_type" />
      <el-table-column label="调度配置" align="center" prop="schedule_conf" :show-overflow-tooltip="true" />
      <el-table-column label="任务状态" align="center" prop="status">
        <template #default="scope">
            <el-tag v-if="scope.row.status === 'running'" type="success">运行中</el-tag>
            <el-tag v-else-if="scope.row.status === 'failed'" type="danger">失败</el-tag>
            <el-tag v-else-if="scope.row.status === 'paused'" type="warning">暂停</el-tag>
            <el-tag v-else type="info">空闲</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="上次运行时间" align="center" prop="last_run_time" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.last_run_time) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="VideoPlay" @click="handleStart(scope.row)" v-if="scope.row.status !== 'running'">启动</el-button>
          <el-button link type="primary" icon="VideoPause" @click="handlePause(scope.row)" v-if="scope.row.status === 'running'">暂停</el-button>
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)">修改</el-button>
          <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)">删除</el-button>
          <el-button link type="primary" icon="Document" @click="handleLog(scope.row)">日志</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total>0"
      :total="total"
      v-model:page="queryParams.page"
      v-model:limit="queryParams.page_size"
      @pagination="getList"
    />

    <!-- 添加或修改任务对话框 -->
    <el-dialog :title="title" v-model="open" width="500px" append-to-body>
      <el-form ref="taskRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="form.task_name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="任务类型" prop="task_type">
          <el-select v-model="form.task_type" placeholder="请选择任务类型">
            <el-option label="数据采集" value="collection" />
            <el-option label="数据同步" value="sync" />
            <el-option label="数据计算" value="calculation" />
            <el-option label="数据存储" value="storage" />
          </el-select>
        </el-form-item>
        <el-form-item label="调度类型" prop="schedule_type">
          <el-radio-group v-model="form.schedule_type">
            <el-radio label="cron">Cron表达式</el-radio>
            <el-radio label="interval">固定间隔</el-radio>
            <el-radio label="once">单次执行</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="调度配置" prop="schedule_conf">
          <el-input v-model="form.schedule_conf" placeholder="请输入Cron表达式或间隔时间(秒)" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="DataTask">
import { listTask, getTask, addTask, updateTask, delTask, startTask, pauseTask } from "@/api/datataskmonitor";
import { parseTime } from "@/utils/ruoyi"; // Assuming this utility exists

const { proxy } = getCurrentInstance();

const taskList = ref([]);
const open = ref(false);
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const total = ref(0);
const title = ref("");

const data = reactive({
  form: {},
  queryParams: {
    page: 1,
    page_size: 10,
    task_name: undefined,
    task_type: undefined,
    status: undefined
  },
  rules: {
    task_name: [{ required: true, message: "任务名称不能为空", trigger: "blur" }],
    task_type: [{ required: true, message: "任务类型不能为空", trigger: "change" }],
    schedule_type: [{ required: true, message: "调度类型不能为空", trigger: "change" }],
    schedule_conf: [{ required: true, message: "调度配置不能为空", trigger: "blur" }]
  }
});

const { queryParams, form, rules } = toRefs(data);

/** 查询任务列表 */
function getList() {
  loading.value = true;
  listTask(queryParams.value).then(response => {
    taskList.value = response.rows; // DRF StandardPagination uses results
    total.value = response.total;
    loading.value = false;
  });
}

/** 取消按钮 */
function cancel() {
  open.value = false;
  reset();
}

/** 表单重置 */
function reset() {
  form.value = {
    id: undefined,
    task_name: undefined,
    task_type: "collection",
    schedule_type: "cron",
    schedule_conf: undefined,
    description: undefined
  };
  proxy.resetForm("taskRef");
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

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.id);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}

/** 新增按钮操作 */
function handleAdd() {
  reset();
  open.value = true;
  title.value = "添加任务";
}

/** 修改按钮操作 */
function handleUpdate(row) {
  reset();
  const taskId = row.id || ids.value;
  getTask(taskId).then(response => {
    form.value = response;
    open.value = true;
    title.value = "修改任务";
  });
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs["taskRef"].validate(valid => {
    if (valid) {
      if (form.value.id != undefined) {
        updateTask(form.value).then(response => {
          proxy.$modal.msgSuccess("修改成功");
          open.value = false;
          getList();
        });
      } else {
        addTask(form.value).then(response => {
          proxy.$modal.msgSuccess("新增成功");
          open.value = false;
          getList();
        });
      }
    }
  });
}

/** 删除按钮操作 */
function handleDelete(row) {
  const taskIds = row.id || ids.value;
  proxy.$modal.confirm('是否确认删除任务编号为"' + taskIds + '"的数据项？').then(function() {
    return delTask(taskIds);
  }).then(() => {
    getList();
    proxy.$modal.msgSuccess("删除成功");
  }).catch(() => {});
}

/** 启动任务 */
function handleStart(row) {
    startTask(row.id).then(() => {
        proxy.$modal.msgSuccess("启动成功");
        getList();
    });
}

/** 暂停任务 */
function handlePause(row) {
    pauseTask(row.id).then(() => {
        proxy.$modal.msgSuccess("暂停成功");
        getList();
    });
}

/** 跳转日志 */
function handleLog(row) {
    // Navigate to log page with query param
    proxy.$router.push({ path: '/datataskmonitor/log', query: { taskId: row.id } });
}

getList();
</script>
