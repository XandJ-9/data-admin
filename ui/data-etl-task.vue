<script setup lang="ts">
import { ref, reactive } from 'vue';
import {
  CheckCircle2, Circle, ChevronRight, ChevronLeft, Save, Play,
  Database, ArrowRightLeft, Settings, LayoutGrid, Server,
  Plus, Trash2, PlayCircle
} from 'lucide-vue-next';

type TaskType = 'sync' | 'sql' | 'procedure';
type ExtractMode = 'full' | 'incremental';
type WriteMode = 'append' | 'overwrite' | 'upsert';

interface ETLTask {
  name: string;
  type: TaskType;
  domain: string;
  sourceType: string;
  sourceInstance: string;
  extractMode: ExtractMode;
  incrementalField: string;
  mappings: { id: string; source: string; target: string }[];
  sqlQuery: string;
  writeMode: WriteMode;
  targetTable: string;
  partition: string;
  scheduleType: string;
  cronExpression: string;
  cpuCore: number;
  memory: number;
  retryCount: number;
  retryInterval: number;
}

const STEPS = [
  { id: 1, title: '基础信息', icon: LayoutGrid, desc: '配置任务名称与类型' },
  { id: 2, title: '源端配置', icon: Database, desc: '选择数据源与抽取方式' },
  { id: 3, title: '转换逻辑', icon: ArrowRightLeft, desc: '字段映射或SQL转换' },
  { id: 4, title: '目标端配置', icon: Server, desc: '配置写入模式与目标表' },
  { id: 5, title: '高级配置', icon: Settings, desc: '调度策略与资源分配' },
];

const currentStep = ref(1);
const task = reactive<ETLTask>({
  name: '',
  type: 'sync',
  domain: 'trade',
  sourceType: 'mysql',
  sourceInstance: '',
  extractMode: 'full',
  incrementalField: '',
  mappings: [
    { id: '1', source: 'id', target: 'id' },
    { id: '2', source: 'user_id', target: 'user_id' },
    { id: '3', source: 'created_at', target: 'created_at' },
  ],
  sqlQuery: "SELECT * FROM source_table WHERE dt = '${biz_date}'",
  writeMode: 'append',
  targetTable: '',
  partition: 'dt=${biz_date}',
  scheduleType: 'daily',
  cronExpression: '0 0 2 * * ?',
  cpuCore: 2,
  memory: 4,
  retryCount: 3,
  retryInterval: 60,
});

const previewData = ref<any[] | null>(null);
const isPreviewing = ref(false);

const handleNext = () => {
  if (currentStep.value < STEPS.length) currentStep.value++;
};

const handlePrev = () => {
  if (currentStep.value > 1) currentStep.value--;
};

const handlePreview = () => {
  isPreviewing.value = true;
  setTimeout(() => {
    previewData.value = [
      { id: 1, user_id: 1001, status: 'active', created_at: '2023-10-01 10:00:00' },
      { id: 2, user_id: 1002, status: 'pending', created_at: '2023-10-01 10:05:00' },
      { id: 3, user_id: 1003, status: 'active', created_at: '2023-10-01 10:10:00' },
    ];
    isPreviewing.value = false;
  }, 800);
};

const addMapping = () => {
  task.mappings.push({ id: Date.now().toString(), source: '', target: '' });
};

const removeMapping = (id: string) => {
  task.mappings = task.mappings.filter(m => m.id !== id);
};

const updateSchedule = (type: string) => {
  task.scheduleType = type;
  if (type === 'daily') task.cronExpression = '0 0 2 * * ?';
  if (type === 'hourly') task.cronExpression = '0 0 * * * ?';
  if (type === 'weekly') task.cronExpression = '0 0 2 ? * MON';
};
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex flex-col font-sans">
    <!-- Header -->
    <header class="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between sticky top-0 z-10 shadow-sm">
      <div class="flex items-center space-x-4">
        <div class="h-8 w-8 bg-indigo-600 rounded-md flex items-center justify-center">
          <Database class="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 class="text-lg font-bold text-slate-900 leading-tight">
            {{ task.name || '新建 ETL 任务' }}
          </h1>
          <div class="text-xs text-slate-500 flex items-center mt-0.5">
            <span class="inline-block w-2 h-2 rounded-full bg-slate-300 mr-1.5"></span>
            草稿状态
          </div>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <div class="flex items-center mr-4">
          <span class="text-sm text-slate-600 mr-2">优先级:</span>
          <select class="text-sm border-slate-300 rounded-md py-1 pl-2 pr-6 focus:ring-indigo-500 focus:border-indigo-500">
            <option>高 (High)</option>
            <option selected>中 (Medium)</option>
            <option>低 (Low)</option>
          </select>
        </div>
        <button class="px-4 py-2 border border-slate-300 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors flex items-center">
          <Save class="h-4 w-4 mr-1.5" /> 保存草稿
        </button>
        <button class="px-4 py-2 bg-indigo-600 rounded-md text-sm font-medium text-white hover:bg-indigo-700 transition-colors flex items-center shadow-sm">
          <Play class="h-4 w-4 mr-1.5" /> 发布任务
        </button>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden max-w-7xl w-full mx-auto">
      <!-- Sidebar -->
      <aside class="w-64 bg-white border-r border-slate-200 overflow-y-auto">
        <div class="p-6">
          <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">配置进度</h3>
          <nav class="space-y-1">
            <div v-for="(step, index) in STEPS" :key="step.id" class="relative">
              <div v-if="index !== STEPS.length - 1" 
                   :class="['absolute left-4 top-10 bottom-[-1rem] w-0.5', currentStep > step.id ? 'bg-indigo-600' : 'bg-slate-200']"></div>
              <button
                @click="currentStep = step.id"
                :class="['w-full flex items-start p-3 rounded-lg text-left transition-colors', currentStep === step.id ? 'bg-indigo-50' : 'hover:bg-slate-50']"
              >
                <div :class="['flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center z-10 relative', 
                  currentStep > step.id ? 'bg-indigo-600 text-white' : 
                  currentStep === step.id ? 'bg-indigo-100 text-indigo-600 border-2 border-indigo-600' : 
                  'bg-white border-2 border-slate-300 text-slate-400']">
                  <CheckCircle2 v-if="currentStep > step.id" class="h-5 w-5" />
                  <span v-else class="text-sm font-medium">{{ step.id }}</span>
                </div>
                <div class="ml-3">
                  <p :class="['text-sm font-medium', currentStep === step.id ? 'text-indigo-900' : currentStep > step.id ? 'text-slate-900' : 'text-slate-500']">
                    {{ step.title }}
                  </p>
                  <p :class="['text-xs mt-0.5', currentStep === step.id ? 'text-indigo-700' : 'text-slate-500']">
                    {{ step.desc }}
                  </p>
                </div>
              </button>
            </div>
          </nav>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="flex-1 flex flex-col bg-white overflow-hidden">
        <div class="flex-1 overflow-y-auto p-8">
          
          <!-- Step 1 -->
          <div v-if="currentStep === 1" class="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 class="text-xl font-semibold text-slate-800 border-b pb-2">基本信息与类型选择</h2>
            <div class="space-y-4 max-w-2xl">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">任务名称 <span class="text-red-500">*</span></label>
                <input v-model="task.name" type="text" placeholder="例如: sync_order_to_dw" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">任务类型 <span class="text-red-500">*</span></label>
                <div class="grid grid-cols-3 gap-3">
                  <div @click="task.type = 'sync'" :class="['cursor-pointer border rounded-md p-3 text-center text-sm font-medium transition-colors', task.type === 'sync' ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-slate-200 hover:border-slate-300 text-slate-600']">数据同步 (E&L)</div>
                  <div @click="task.type = 'sql'" :class="['cursor-pointer border rounded-md p-3 text-center text-sm font-medium transition-colors', task.type === 'sql' ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-slate-200 hover:border-slate-300 text-slate-600']">SQL转换 (T)</div>
                  <div @click="task.type = 'procedure'" :class="['cursor-pointer border rounded-md p-3 text-center text-sm font-medium transition-colors', task.type === 'procedure' ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-slate-200 hover:border-slate-300 text-slate-600']">存储过程</div>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">所属业务域 <span class="text-red-500">*</span></label>
                <select v-model="task.domain" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white">
                  <option value="trade">交易域</option>
                  <option value="user">用户域</option>
                  <option value="logistics">物流域</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Step 2 -->
          <div v-else-if="currentStep === 2" class="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 class="text-xl font-semibold text-slate-800 border-b pb-2">源端 (Source) 配置</h2>
            <div class="space-y-4 max-w-2xl">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">数据源类型</label>
                  <select v-model="task.sourceType" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white">
                    <option value="mysql">MySQL</option>
                    <option value="postgresql">PostgreSQL</option>
                    <option value="hive">Hive</option>
                    <option value="kafka">Kafka</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">连接配置 (实例别名)</label>
                  <select v-model="task.sourceInstance" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white">
                    <option value="" disabled>请选择实例...</option>
                    <option value="prod-db-01">prod-db-01 (主库)</option>
                    <option value="prod-db-ro-01">prod-db-ro-01 (只读库)</option>
                    <option value="dev-db-01">dev-db-01 (测试库)</option>
                  </select>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">抽取方式</label>
                <div class="flex items-center space-x-4">
                  <label class="flex items-center">
                    <input type="radio" v-model="task.extractMode" value="full" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300" />
                    <span class="ml-2 text-sm text-slate-700">全量抽取</span>
                  </label>
                  <label class="flex items-center">
                    <input type="radio" v-model="task.extractMode" value="incremental" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300" />
                    <span class="ml-2 text-sm text-slate-700">增量抽取</span>
                  </label>
                </div>
              </div>
              <div v-if="task.extractMode === 'incremental'" class="animate-in fade-in zoom-in-95 duration-200">
                <label class="block text-sm font-medium text-slate-700 mb-1">增量字段</label>
                <input v-model="task.incrementalField" type="text" placeholder="例如: updated_at" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                <p class="mt-1 text-xs text-slate-500">系统将基于此字段的增量值进行数据抽取。</p>
              </div>
              <div class="pt-4 border-t">
                <button @click="handlePreview" :disabled="isPreviewing || !task.sourceInstance" class="flex items-center px-4 py-2 border border-slate-300 shadow-sm text-sm font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50">
                  <div v-if="isPreviewing" class="h-4 w-4 mr-2 rounded-full border-2 border-slate-300 border-t-indigo-600 animate-spin"></div>
                  <PlayCircle v-else class="h-4 w-4 mr-2 text-indigo-500" />
                  预览数据 (前10行)
                </button>
                <div v-if="previewData" class="mt-4 overflow-x-auto border rounded-md">
                  <table class="min-w-full divide-y divide-slate-200">
                    <thead class="bg-slate-50">
                      <tr>
                        <th v-for="key in Object.keys(previewData[0])" :key="key" class="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                          {{ key }}
                        </th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-slate-200">
                      <tr v-for="(row, i) in previewData" :key="i">
                        <td v-for="(val, j) in Object.values(row)" :key="j" class="px-4 py-2 whitespace-nowrap text-sm text-slate-600">
                          {{ val }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3 -->
          <div v-else-if="currentStep === 3" class="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 class="text-xl font-semibold text-slate-800 border-b pb-2">转换/映射 (Transform/Mapping)</h2>
            <div v-if="task.type === 'sync'" class="space-y-4">
              <div class="flex justify-between items-center">
                <h3 class="text-sm font-medium text-slate-700">字段映射 (Field Mapping)</h3>
                <button class="text-sm text-indigo-600 hover:text-indigo-800 font-medium">自动匹配同名字段</button>
              </div>
              <div class="border rounded-md overflow-hidden">
                <div class="grid grid-cols-[1fr_auto_1fr_auto] gap-4 bg-slate-50 p-3 border-b text-sm font-medium text-slate-600">
                  <div>源端字段 (Source)</div>
                  <div class="w-8"></div>
                  <div>目标端字段 (Target)</div>
                  <div class="w-8"></div>
                </div>
                <div class="divide-y max-h-[400px] overflow-y-auto">
                  <div v-for="mapping in task.mappings" :key="mapping.id" class="grid grid-cols-[1fr_auto_1fr_auto] gap-4 p-3 items-center bg-white hover:bg-slate-50">
                    <input v-model="mapping.source" type="text" class="px-2 py-1 border rounded text-sm focus:ring-indigo-500 focus:border-indigo-500" />
                    <ArrowRightLeft class="h-4 w-4 text-slate-400" />
                    <input v-model="mapping.target" type="text" class="px-2 py-1 border rounded text-sm focus:ring-indigo-500 focus:border-indigo-500" />
                    <button @click="removeMapping(mapping.id)" class="text-slate-400 hover:text-red-500">
                      <Trash2 class="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <div class="p-3 bg-slate-50 border-t">
                  <button @click="addMapping" class="flex items-center text-sm text-indigo-600 hover:text-indigo-800 font-medium">
                    <Plus class="h-4 w-4 mr-1" /> 添加映射
                  </button>
                </div>
              </div>
            </div>
            <div v-else class="space-y-4">
              <div class="flex justify-between items-center">
                <h3 class="text-sm font-medium text-slate-700">SQL 转换逻辑</h3>
                <button class="text-sm text-indigo-600 hover:text-indigo-800 font-medium">格式化 SQL</button>
              </div>
              <div class="relative border rounded-md overflow-hidden bg-slate-900">
                <div class="flex items-center px-4 py-2 bg-slate-800 text-slate-300 text-xs font-mono border-b border-slate-700">
                  <span class="text-emerald-400 mr-2">SQL</span>
                  <span>Editor</span>
                </div>
                <textarea v-model="task.sqlQuery" class="w-full h-64 p-4 bg-slate-900 text-slate-100 font-mono text-sm focus:outline-none resize-none" spellcheck="false"></textarea>
              </div>
              <p class="text-xs text-slate-500">支持使用 <code class="bg-slate-100 px-1 rounded text-pink-600">${'{var}'}</code> 语法引用调度变量。</p>
            </div>
          </div>

          <!-- Step 4 -->
          <div v-else-if="currentStep === 4" class="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 class="text-xl font-semibold text-slate-800 border-b pb-2">目标端 (Sink) 配置</h2>
            <div class="space-y-4 max-w-2xl">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">写入模式</label>
                <div class="grid grid-cols-3 gap-3">
                  <div @click="task.writeMode = 'append'" :class="['cursor-pointer border rounded-md p-3 transition-colors', task.writeMode === 'append' ? 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500' : 'border-slate-200 hover:border-slate-300']">
                    <div :class="['text-sm font-medium', task.writeMode === 'append' ? 'text-indigo-700' : 'text-slate-700']">追加 (Append)</div>
                    <div class="text-xs text-slate-500 mt-1">直接插入新数据</div>
                  </div>
                  <div @click="task.writeMode = 'overwrite'" :class="['cursor-pointer border rounded-md p-3 transition-colors', task.writeMode === 'overwrite' ? 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500' : 'border-slate-200 hover:border-slate-300']">
                    <div :class="['text-sm font-medium', task.writeMode === 'overwrite' ? 'text-indigo-700' : 'text-slate-700']">覆盖 (Overwrite)</div>
                    <div class="text-xs text-slate-500 mt-1">清空分区后插入</div>
                  </div>
                  <div @click="task.writeMode = 'upsert'" :class="['cursor-pointer border rounded-md p-3 transition-colors', task.writeMode === 'upsert' ? 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500' : 'border-slate-200 hover:border-slate-300']">
                    <div :class="['text-sm font-medium', task.writeMode === 'upsert' ? 'text-indigo-700' : 'text-slate-700']">更新 (Upsert)</div>
                    <div class="text-xs text-slate-500 mt-1">按主键更新或插入</div>
                  </div>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">目标表</label>
                <div class="relative">
                  <input v-model="task.targetTable" type="text" placeholder="搜索数仓表结构 (例如: dwd_trade_order_di)" class="w-full px-3 py-2 pl-10 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                  <Database class="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">分区设置</label>
                <input v-model="task.partition" type="text" placeholder="例如: dt=${biz_date}" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm font-mono" />
                <p class="mt-1 text-xs text-slate-500">支持变量填入，如 <code class="bg-slate-100 px-1 rounded">dt=${'{biz_date}'}</code>。</p>
              </div>
            </div>
          </div>

          <!-- Step 5 -->
          <div v-else-if="currentStep === 5" class="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 class="text-xl font-semibold text-slate-800 border-b pb-2">高级与调度配置</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div class="space-y-4">
                <h3 class="text-sm font-medium text-slate-800 bg-slate-100 px-3 py-2 rounded">调度策略</h3>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">执行周期</label>
                  <select :value="task.scheduleType" @change="e => updateSchedule((e.target as HTMLSelectElement).value)" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white">
                    <option value="daily">每天 (例如: 凌晨2点)</option>
                    <option value="hourly">每小时</option>
                    <option value="weekly">每周</option>
                    <option value="custom">自定义 Cron</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Cron 表达式</label>
                  <input v-model="task.cronExpression" @input="task.scheduleType = 'custom'" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm font-mono text-indigo-600" />
                  <div class="mt-2 text-xs text-slate-500 bg-slate-50 p-2 rounded border">
                    预计下次执行时间: <span class="font-medium text-slate-700">2023-10-25 02:00:00</span>
                  </div>
                </div>
              </div>
              <div class="space-y-4">
                <h3 class="text-sm font-medium text-slate-800 bg-slate-100 px-3 py-2 rounded">资源与容错</h3>
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">CPU Core</label>
                    <select v-model.number="task.cpuCore" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white">
                      <option :value="1">1 Core</option>
                      <option :value="2">2 Cores</option>
                      <option :value="4">4 Cores</option>
                      <option :value="8">8 Cores</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Memory</label>
                    <select v-model.number="task.memory" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white">
                      <option :value="2">2 GB</option>
                      <option :value="4">4 GB</option>
                      <option :value="8">8 GB</option>
                      <option :value="16">16 GB</option>
                    </select>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">失败重试次数</label>
                    <input v-model.number="task.retryCount" type="number" min="0" max="10" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">重试间隔 (秒)</label>
                    <input v-model.number="task.retryInterval" type="number" min="0" class="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
        
        <!-- Footer Navigation -->
        <div class="p-6 bg-slate-50 border-t border-slate-200 flex justify-between items-center">
          <button
            @click="handlePrev"
            :disabled="currentStep === 1"
            :class="['px-4 py-2 border border-slate-300 rounded-md text-sm font-medium flex items-center transition-colors', currentStep === 1 ? 'bg-slate-100 text-slate-400 cursor-not-allowed' : 'bg-white text-slate-700 hover:bg-slate-50']"
          >
            <ChevronLeft class="h-4 w-4 mr-1" /> 上一步
          </button>
          
          <div class="flex space-x-2">
            <div v-for="s in STEPS" :key="s.id" :class="['h-2 w-2 rounded-full', s.id === currentStep ? 'bg-indigo-600' : s.id < currentStep ? 'bg-indigo-300' : 'bg-slate-300']"></div>
          </div>

          <button
            @click="handleNext"
            :disabled="currentStep === STEPS.length"
            :class="['px-4 py-2 border border-transparent rounded-md text-sm font-medium flex items-center transition-colors', currentStep === STEPS.length ? 'bg-indigo-300 text-white cursor-not-allowed' : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm']"
          >
            下一步 <ChevronRight class="h-4 w-4 ml-1" />
          </button>
        </div>
      </main>
    </div>
  </div>
</template>
