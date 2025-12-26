<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="任务名称" prop="taskName">
        <el-input
          v-model="queryParams.taskName"
          placeholder="请输入任务名称"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="来源类型" prop="sourceTaskType">
        <el-select v-model="queryParams.sourceTaskType" placeholder="请选择来源类型" clearable style="width: 240px">
          <el-option label="数据采集" value="data_integration" />
          <el-option label="Hive计算" value="hive" />
          <el-option label="Spark计算" value="spark" />
          <el-option label="SparkSQL计算" value="spark_sql" />
          <el-option label="Flink计算" value="flink" />
          <el-option label="FlinkSQL计算" value="flink_sql" />
          <el-option label="Python脚本" value="python" />
          <el-option label="Shell脚本" value="shell" />
        </el-select>
      </el-form-item>
      <el-form-item label="任务类型" prop="taskType">
        <el-select v-model="queryParams.taskType" placeholder="请选择任务类型" clearable style="width: 240px">
          <el-option label="数据采集" value="collection" />
          <el-option label="数据同步" value="sync" />
          <el-option label="数据计算" value="calculation" />
          <el-option label="数据存储" value="storage" />
        </el-select>
      </el-form-item>
      <el-form-item label="启用状态" prop="enabled">
        <el-select v-model="queryParams.enabled" placeholder="请选择启用状态" clearable style="width: 240px">
          <el-option label="启用" value="0" />
          <el-option label="禁用" value="1" />
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
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="taskList" @selection-change="handleSelectionChange">
      <el-table-column label="任务编号" align="center" prop="id" width="90" />
      <el-table-column label="任务名称" align="center" prop="taskName" :show-overflow-tooltip="true" />
      <el-table-column label="来源类型" align="center" prop="sourceTaskType" width="120">
        <template #default="scope">
          <el-tag v-if="scope.row.sourceTaskType === 'data_integration'">采集</el-tag>
          <el-tag v-else-if="scope.row.sourceTaskType === 'hive'" type="warning">Hive</el-tag>
          <el-tag v-else-if="scope.row.sourceTaskType === 'spark'" type="warning">Spark</el-tag>
          <el-tag v-else-if="scope.row.sourceTaskType === 'spark_sql'" type="warning">SparkSQL</el-tag>
          <el-tag v-else-if="scope.row.sourceTaskType === 'flink'" type="warning">Flink</el-tag>
          <el-tag v-else-if="scope.row.sourceTaskType === 'flink_sql'" type="warning">FlinkSQL</el-tag>
          <el-tag v-else-if="scope.row.sourceTaskType === 'python'" type="success">Python</el-tag>
          <el-tag v-else-if="scope.row.sourceTaskType === 'shell'" type="success">Shell</el-tag>
          <el-tag v-else type="info">{{ scope.row.sourceTaskType || '-' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="任务类型" align="center" prop="taskType">
        <template #default="scope">
           <el-tag v-if="scope.row.taskType === 'collection'">数据采集</el-tag>
           <el-tag v-else-if="scope.row.taskType === 'sync'" type="success">数据同步</el-tag>
           <el-tag v-else-if="scope.row.taskType === 'calculation'" type="warning">数据计算</el-tag>
           <el-tag v-else type="info">数据存储</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="启用" align="center" prop="enabled" width="90">
        <template #default="scope">
          <el-switch
            v-model="scope.row.enabled"
            active-value="0"
            inactive-value="1"
            @change="handleEnabledChange(scope.row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="调度类型" align="center" prop="scheduleType" width="120">
        <template #default="scope">
          <span>{{ scheduleTypeLabel(scope.row.scheduleType) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="调度配置" align="center" prop="scheduleConf" :show-overflow-tooltip="true" />
      <el-table-column label="任务状态" align="center" prop="status">
        <template #default="scope">
            <el-tag v-if="scope.row.status === 'running'" type="success">运行中</el-tag>
            <el-tag v-else-if="scope.row.status === 'failed'" type="danger">失败</el-tag>
            <el-tag v-else-if="scope.row.status === 'paused'" type="warning">暂停</el-tag>
            <el-tag v-else-if="scope.row.status === 'success'" type="success">成功</el-tag>
            <el-tag v-else type="info">空闲</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="上次运行时间" align="center" prop="lastRunTime" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.lastRunTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="下次运行时间" align="center" prop="nextRunTime" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.nextRunTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width" width="240">
        <template #default="scope">
          <el-button link type="primary" icon="VideoPlay" @click="handleStart(scope.row)" v-if="scope.row.status !== 'running'">启动</el-button>
          <el-button link type="primary" icon="VideoPause" @click="handlePause(scope.row)" v-if="scope.row.status === 'running'">暂停</el-button>
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)">配置</el-button>
          <el-button link type="primary" icon="Document" @click="handleLog(scope.row)">日志</el-button>
          <el-button link type="primary" icon="Bell" @click="openRule(scope.row)">报警规则</el-button>
          <el-button link type="primary" icon="Warning" @click="openAlert(scope.row)">报警记录</el-button>
          <el-button link type="primary" icon="Link" @click="openSourceTask(scope.row)" v-if="scope.row.sourceTaskId">开发任务</el-button>
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

    <!-- 添加或修改任务对话框 -->
    <el-dialog :title="title" v-model="open" width="500px" append-to-body>
      <el-form ref="taskRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="任务名称">
          <el-input v-model="form.taskName" disabled />
        </el-form-item>
        <el-form-item label="启用状态" prop="enabled">
          <el-radio-group v-model="form.enabled">
            <el-radio label="0">启用</el-radio>
            <el-radio label="1">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="调度类型" prop="scheduleType">
          <el-radio-group v-model="form.scheduleType">
            <el-radio label="once">手动</el-radio>
            <el-radio label="cron">定时(Cron)</el-radio>
            <el-radio label="interval">固定间隔</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="调度配置" prop="scheduleConf">
          <el-input v-model="form.scheduleConf" :disabled="form.scheduleType === 'once'" placeholder="Cron表达式 或 间隔秒数" />
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

    <el-dialog title="报警规则" v-model="ruleOpen" width="900px" append-to-body>
      <el-row :gutter="10" class="mb8">
        <el-col :span="1.5">
          <el-button type="primary" plain icon="Plus" @click="openRuleForm()">新增</el-button>
        </el-col>
      </el-row>
      <el-table v-loading="ruleLoading" :data="ruleList">
        <el-table-column label="规则名称" prop="ruleName" :show-overflow-tooltip="true" />
        <el-table-column label="类型" prop="ruleType" width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.ruleType === 'failure'" type="danger">失败</el-tag>
            <el-tag v-else type="warning">超时</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="阈值" prop="threshold" width="100" />
        <el-table-column label="渠道" prop="notificationChannels" :show-overflow-tooltip="true" />
        <el-table-column label="接收人" prop="receivers" :show-overflow-tooltip="true" />
        <el-table-column label="启用" prop="isActive" width="90">
          <template #default="scope">
            <el-tag v-if="scope.row.isActive" type="success">是</el-tag>
            <el-tag v-else type="info">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="scope">
            <el-button link type="primary" icon="Edit" @click="openRuleForm(scope.row)">修改</el-button>
            <el-button link type="primary" icon="Delete" @click="deleteRule(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <pagination
        v-show="ruleTotal>0"
        :total="ruleTotal"
        v-model:page="ruleQuery.pageNum"
        v-model:limit="ruleQuery.pageSize"
        @pagination="getRuleList"
      />
    </el-dialog>

    <el-dialog :title="ruleTitle" v-model="ruleFormOpen" width="520px" append-to-body>
      <el-form ref="ruleRef" :model="ruleForm" :rules="ruleRules" label-width="100px">
        <el-form-item label="规则名称" prop="ruleName">
          <el-input v-model="ruleForm.ruleName" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="规则类型" prop="ruleType">
          <el-select v-model="ruleForm.ruleType" placeholder="请选择类型" style="width: 100%">
            <el-option label="任务失败" value="failure" />
            <el-option label="运行超时" value="timeout" />
          </el-select>
        </el-form-item>
        <el-form-item label="阈值" prop="threshold">
          <el-input v-model.number="ruleForm.threshold" placeholder="请输入阈值(秒/次数)" />
        </el-form-item>
        <el-form-item label="通知渠道" prop="notificationChannels">
          <el-select v-model="ruleChannels" multiple placeholder="请选择渠道" style="width: 100%">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="微信" value="wechat" />
          </el-select>
        </el-form-item>
        <el-form-item label="接收人" prop="receivers">
          <el-input v-model="ruleForm.receivers" placeholder="逗号分隔" />
        </el-form-item>
        <el-form-item label="是否启用" prop="isActive">
          <el-switch v-model="ruleForm.isActive" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitRuleForm">确 定</el-button>
          <el-button @click="cancelRuleForm">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog title="报警记录" v-model="alertOpen" width="980px" append-to-body>
      <el-table v-loading="alertLoading" :data="alertList">
        <el-table-column label="触发时间" prop="triggerTime" width="180">
          <template #default="scope">
            <span>{{ parseTime(scope.row.triggerTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="规则" prop="ruleName" width="160" :show-overflow-tooltip="true" />
        <el-table-column label="内容" prop="content" :show-overflow-tooltip="true" />
        <el-table-column label="状态" prop="status" width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.status === 'pending'" type="warning">待处理</el-tag>
            <el-tag v-else-if="scope.row.status === 'handled'" type="success">已处理</el-tag>
            <el-tag v-else type="info">已忽略</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="处理时间" prop="handleTime" width="180">
          <template #default="scope">
            <span>{{ parseTime(scope.row.handleTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="处理备注" prop="handleNote" width="200" :show-overflow-tooltip="true" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button link type="primary" icon="Check" v-if="scope.row.status === 'pending'" @click="handleAlertRecord(scope.row)">处理</el-button>
          </template>
        </el-table-column>
      </el-table>
      <pagination
        v-show="alertTotal>0"
        :total="alertTotal"
        v-model:page="alertQuery.pageNum"
        v-model:limit="alertQuery.pageSize"
        @pagination="getAlertList"
      />
    </el-dialog>
  </div>
</template>

<script setup name="DataTask">
import { listTask, getTask, updateTask, startTask, pauseTask, listAlertRule, addAlertRule, updateAlertRule, delAlertRule, listAlertRecord, handleAlert } from "@/api/datataskmonitor";
import { parseTime } from "@/utils/ruoyi";
import { useRouter } from "vue-router";

const { proxy } = getCurrentInstance();
const router = useRouter();

const taskList = ref([]);
const open = ref(false);
const loading = ref(true);
const showSearch = ref(true);
const total = ref(0);
const title = ref("");

const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    taskName: undefined,
    taskType: undefined,
    enabled: undefined,
    sourceTaskType: undefined,
    status: undefined
  },
  rules: {
    enabled: [{ required: true, message: "启用状态不能为空", trigger: "change" }],
    scheduleType: [{ required: true, message: "调度类型不能为空", trigger: "change" }],
    scheduleConf: [
      {
        validator: (rule, value, callback) => {
          if (form.value.scheduleType === "once") return callback();
          if (!value) return callback(new Error("调度配置不能为空"));
          return callback();
        },
        trigger: "blur"
      }
    ]
  }
});

const { queryParams, form, rules } = toRefs(data);

/** 查询任务列表 */
function getList() {
  loading.value = true;
  listTask(queryParams.value).then(response => {
    taskList.value = response.rows || [];
    total.value = response.total || 0;
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
    taskName: undefined,
    scheduleType: "once",
    scheduleConf: "",
    enabled: "0",
    description: ""
  };
  proxy.resetForm("taskRef");
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

/** 多选框选中数据 */
function handleSelectionChange() {}

/** 修改按钮操作 */
function handleUpdate(row) {
  reset();
  const taskId = row.id;
  getTask(taskId).then(response => {
    form.value = response.data || {};
    open.value = true;
    title.value = "任务配置";
  });
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs["taskRef"].validate(valid => {
    if (valid) {
      updateTask(form.value).then(() => {
        proxy.$modal.msgSuccess("修改成功");
        open.value = false;
        getList();
      });
    }
  });
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
    proxy.$router.push({ path: '/datataskmonitor/log', query: { taskId: row.id } });
}

function scheduleTypeLabel(v) {
  if (v === "once") return "手动";
  if (v === "cron") return "定时(Cron)";
  if (v === "interval") return "固定间隔";
  return v || "-";
}

function handleEnabledChange(row) {
  const payload = {
    id: row.id,
    enabled: row.enabled,
    scheduleType: row.scheduleType || "once",
    scheduleConf: row.scheduleConf || "",
    description: row.description || ""
  };
  updateTask(payload).then(() => {
    proxy.$modal.msgSuccess("状态已更新");
    getList();
  }).catch(() => {
    getList();
  });
}

function openSourceTask(row) {
  if (!row?.sourceTaskId) return;
  router.push(`/datastudio/task-detail/${row.sourceTaskId}`);
}

const currentTask = ref(null);

const ruleOpen = ref(false);
const ruleLoading = ref(false);
const ruleList = ref([]);
const ruleTotal = ref(0);
const ruleQuery = reactive({ pageNum: 1, pageSize: 10, taskId: undefined });
const ruleFormOpen = ref(false);
const ruleTitle = ref("");
const ruleForm = ref({});
const ruleChannels = ref([]);
const ruleRules = {
  ruleName: [{ required: true, message: "规则名称不能为空", trigger: "blur" }],
  ruleType: [{ required: true, message: "规则类型不能为空", trigger: "change" }],
  receivers: [{ required: true, message: "接收人不能为空", trigger: "blur" }]
};

function getRuleList() {
  ruleLoading.value = true;
  listAlertRule(ruleQuery).then(res => {
    ruleList.value = res.rows || [];
    ruleTotal.value = res.total || 0;
    ruleLoading.value = false;
  }).catch(() => (ruleLoading.value = false));
}

function openRule(row) {
  currentTask.value = row;
  ruleQuery.pageNum = 1;
  ruleQuery.taskId = row.id;
  ruleOpen.value = true;
  getRuleList();
}

function resetRuleForm() {
  ruleForm.value = {
    id: undefined,
    taskId: currentTask.value?.id,
    ruleName: "",
    ruleType: "failure",
    threshold: 0,
    notificationChannels: "",
    receivers: "",
    isActive: true
  };
  ruleChannels.value = [];
  proxy.resetForm("ruleRef");
}

function openRuleForm(row) {
  resetRuleForm();
  if (row?.id) {
    ruleForm.value = { ...row };
    ruleChannels.value = (row.notificationChannels || "").split(",").filter(Boolean);
    ruleTitle.value = "修改规则";
  } else {
    ruleTitle.value = "新增规则";
  }
  ruleFormOpen.value = true;
}

function cancelRuleForm() {
  ruleFormOpen.value = false;
  resetRuleForm();
}

function submitRuleForm() {
  proxy.$refs["ruleRef"].validate(valid => {
    if (!valid) return;
    ruleForm.value.notificationChannels = (ruleChannels.value || []).join(",");
    ruleForm.value.taskId = currentTask.value?.id;
    if (ruleForm.value.id) {
      updateAlertRule(ruleForm.value).then(() => {
        proxy.$modal.msgSuccess("修改成功");
        ruleFormOpen.value = false;
        getRuleList();
      });
    } else {
      addAlertRule(ruleForm.value).then(() => {
        proxy.$modal.msgSuccess("新增成功");
        ruleFormOpen.value = false;
        getRuleList();
      });
    }
  });
}

function deleteRule(row) {
  proxy.$modal.confirm(`是否确认删除规则"${row.ruleName}"？`).then(() => {
    return delAlertRule(row.id);
  }).then(() => {
    proxy.$modal.msgSuccess("删除成功");
    getRuleList();
  }).catch(() => {});
}

const alertOpen = ref(false);
const alertLoading = ref(false);
const alertList = ref([]);
const alertTotal = ref(0);
const alertQuery = reactive({ pageNum: 1, pageSize: 10, taskName: undefined });

function getAlertList() {
  alertLoading.value = true;
  listAlertRecord(alertQuery).then(res => {
    alertList.value = res.rows || [];
    alertTotal.value = res.total || 0;
    alertLoading.value = false;
  }).catch(() => (alertLoading.value = false));
}

function openAlert(row) {
  currentTask.value = row;
  alertQuery.pageNum = 1;
  alertQuery.taskName = row.taskName;
  alertOpen.value = true;
  getAlertList();
}

function handleAlertRecord(row) {
  proxy.$modal.prompt("请输入处理备注").then(({ value }) => {
    return handleAlert(row.id, { note: value || "" });
  }).then(() => {
    proxy.$modal.msgSuccess("处理成功");
    getAlertList();
  }).catch(() => {});
}

getList();
</script>
