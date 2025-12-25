<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="任务名称" prop="name">
        <el-input
          v-model="queryParams.name"
          placeholder="请输入任务名称"
          clearable
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="任务类型" prop="type">
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
      <el-table-column label="任务编号" align="center" prop="id" />
      <el-table-column label="任务名称" align="center" prop="name" />
      <el-table-column label="任务类型" align="center" prop="type">
        <template #default="scope">
          <dict-tag :options="taskTypeOptions" :value="scope.row.type" />
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
      <el-table-column label="创建时间" align="center" prop="create_time" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.create_time) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button
            link
            type="primary"
            icon="Edit"
            @click="handleUpdate(scope.row)"
          >修改</el-button>
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
      v-model:page="queryParams.page"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 添加对话框 -->
    <!-- <el-dialog :title="title" v-model="open" width="500px" append-to-body>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="任务类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择任务类型">
            <el-option
              v-for="dict in taskTypeOptions"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog> -->
  </div>
</template>

<script setup name="DataStudio">
import { listTasks, delTask, addTask } from "@/api/datastudio";
import { ref, reactive, toRefs, getCurrentInstance } from 'vue';
import { useRouter } from 'vue-router';

const { proxy } = getCurrentInstance();
const router = useRouter();

const taskList = ref([]);
const open = ref(false);
const loading = ref(true);
const showSearch = ref(true);
const title = ref("");
const total = ref(0);

const taskTypeOptions = [
  { value: 'data_integration', label: '数据采集' },
  { value: 'hive', label: 'Hive计算' },
  { value: 'spark', label: 'Spark计算' },
  { value: 'flink', label: 'Flink计算' },
  { value: 'python', label: 'Python脚本' },
  { value: 'shell', label: 'Shell脚本' }
];

const data = reactive({
  form: {},
  queryParams: {
    page: 1,
    pageSize: 10,
    name: undefined,
    type: undefined,
    status: undefined
  },
  rules: {
    name: [
      { required: true, message: "任务名称不能为空", trigger: "blur" }
    ],
    type: [
      { required: true, message: "任务类型不能为空", trigger: "change" }
    ]
  }
});

const { queryParams, form, rules } = toRefs(data);

/** 查询列表 */
function getList() {
  loading.value = true;
  listTasks(queryParams.value).then(response => {
    taskList.value = response.rows;
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
    name: undefined,
    type: undefined,
    status: "0"
  };
  proxy.resetForm("formRef");
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

/** 新增按钮操作 */
function handleAdd() {
  reset();
  open.value = true;
    //   title.value = "选择任务类型";
  router.push({ name: 'DataStudioTaskDetail', params: { id: 'new' }, query: { type: form.value.type, name: form.value.name }});
}

/** 修改按钮操作 */
function handleUpdate(row) {
  // 跳转到详情页
  // Since we don't have dynamic routes set up in DB yet, we might need to rely on a known route.
  // Assuming we will add a route /datastudio/task/:id
   router.push({ name: 'DataStudioTaskDetail', params: { id: row.id }, query: { type: form.value.type, name: form.value.name }});

}

/** 删除按钮操作 */
function handleDelete(row) {
  const ids = row.id || ids.value;
  proxy.$modal.confirm('是否确认删除任务编号为"' + ids + '"的数据项？').then(function() {
    return delTask(ids);
  }).then(() => {
    getList();
    proxy.$modal.msgSuccess("删除成功");
  }).catch(() => {});
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs["formRef"].validate(valid => {
    if (valid) {
      // Navigate to detail page with new data
      open.value = false;
       router.push({ name: 'DataStudioTaskDetail', params: { id: form.value.id }, query: { type: form.value.type, name: form.value.name }});
    }
  });
}

getList();
</script>
