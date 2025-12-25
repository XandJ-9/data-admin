<template>
  <div class="app-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ title }}</span>
          <el-button style="float: right; padding: 3px 0" text @click="handleBack">返回</el-button>
        </div>
      </template>
      
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row>
          <el-col :span="12">
            <el-form-item label="任务名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入任务名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务类型" prop="type">
              <el-select v-model="form.type" :disabled="form.id !== 'new'" placeholder="请选择任务类型">
                <el-option
                  v-for="dict in taskTypeOptions"
                  :key="dict.value"
                  :label="dict.label"
                  :value="dict.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="任务描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入任务描述" />
        </el-form-item>

        <el-divider content-position="left">任务配置</el-divider>

        <!-- Dynamic Component based on Task Type -->
        <component 
          :is="getComponent(form.type)" 
          v-model="form.config"
          v-if="form.type"
          :detail="form.config" 
          @update:detail="val => form.config = val"
        />

      </el-form>
        <template #footer>
          <el-button type="primary" @click="submitForm">保存</el-button>
          <el-button @click="handleBack">取消</el-button>
        </template>
    </el-card>
  </div>
</template>

<script setup name="DataStudioTaskDetail">
import { ref, reactive, toRefs, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { addTask, getTask, updateTask } from "@/api/datastudio";
import { getCurrentInstance } from 'vue';

// Import Components
import SyncConfigDetail from '@/views/dataintegration/components/SyncConfigDetail.vue';
import HiveConfig from './components/HiveConfig.vue';
import SparkConfig from './components/SparkConfig.vue';
import SparkSqlConfig from './components/SparkSqlConfig.vue';
import FlinkConfig from './components/FlinkConfig.vue';
import PythonConfig from './components/PythonConfig.vue';
import ShellConfig from './components/ShellConfig.vue';

const { proxy } = getCurrentInstance();
const router = useRouter();
const route = useRoute();

const title = ref("创建任务");
const loading = ref(false);

const taskTypeOptions = [
  { value: 'data_integration', label: '数据采集' },
  { value: 'hive', label: 'Hive计算' },
  { value: 'spark', label: 'Spark计算' },
  { value: 'spark_sql', label: 'SparkSQL计算' },
  { value: 'flink', label: 'Flink计算' },
  { value: 'python', label: 'Python脚本' },
  { value: 'shell', label: 'Shell脚本' }
];

const data = reactive({
    form: {
    id: route.params.id,
    name: '',
    type: '',
    description: '',
    config: {}
  },
  rules: {
    name: [
      { required: true, message: "任务名称不能为空", trigger: "blur" }
    ],
    type: [
      { required: true, message: "任务类型不能为空", trigger: "blur" }
    ]
  }
});

const { form, rules } = toRefs(data);

function getComponent(type) {
  switch (type) {
    case 'data_integration': return SyncConfigDetail;
    case 'hive': return HiveConfig;
    case 'spark': return SparkConfig;
    case 'spark_sql': return SparkSqlConfig;
    case 'flink': return FlinkConfig;
    case 'python': return PythonConfig;
    case 'shell': return ShellConfig;
    default: return null;
  }
}

watch(() => form.value.type, (newType) => {
  const taskId = route.params.id;
  if (taskId && taskId !== 'new') return;

  if (newType === 'data_integration') {
    form.value.config = {
      source: {},
      target: {},
      sourceColumns: [],
      targetColumns: [],
      fieldMappings: [],
      syncConfig: { mode: { type: 'full' } }
    };
  } else if (['hive', 'spark_sql', 'flink'].includes(newType)) {
    form.value.config = { sql: '' };
  } else if (['spark'].includes(newType)) {
    form.value.config = { appName: '', mainClass: '', jar: '', args: '' };
  } else if (['python', 'shell'].includes(newType)) {
    form.value.config = { script: '' };
  } else {
    form.value.config = {};
  }
});


onMounted(() => {
  const taskId = route.params.id;
  const taskType = route.query.type;
  const taskName = route.query.name;

  if (taskId && taskId !== 'new') {
    title.value = "修改任务";
    loading.value = true;
    getTask(taskId).then(res => {
      form.value = res.data;
      if (!form.value.config) form.value.config = {};
      loading.value = false;
    });
  } else {
    form.value.type = taskType;
    if (taskName) form.value.name = taskName;
    // Initialize config based on type if needed
    if (form.value.type === 'data_integration') {
      form.value.config = {
        source: {},
        target: {},
        sourceColumns: [],
        targetColumns: [],
        fieldMappings: [],
        syncConfig: { mode: { type: 'full' } }
      };
    } else if (['hive', 'spark_sql', 'flink'].includes(form.value.type)) {
      form.value.config = { sql: '' };
    } else if (['spark'].includes(form.value.type)) {
      form.value.config = { appName: '', mainClass: '', jar: '', args: '' };
    } else if (['python', 'shell'].includes(form.value.type)) {
      form.value.config = { script: '' };
    } else {
      form.value.config = {};
    }
  }
});

function submitForm() {
  proxy.$refs["formRef"].validate(valid => {
    if (valid) {
      if (form.value.id) {
        updateTask(form.value.id, form.value).then(response => {
          proxy.$modal.msgSuccess("修改成功");
          handleBack();
        });
      } else {
        addTask(form.value).then(response => {
          proxy.$modal.msgSuccess("新增成功");
          handleBack();
        });
      }
    }
  });
}

function handleBack() {
  router.push('/datastudio/index');
}
</script>
