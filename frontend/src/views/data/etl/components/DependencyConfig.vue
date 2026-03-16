<template>
  <div class="dependency-config">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-title">
            <el-icon><Link /></el-icon>
            任务依赖配置
          </span>
          <el-button type="primary" size="small" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加依赖
          </el-button>
        </div>
      </template>

      <!-- 依赖列表 -->
      <div v-if="dependencies.length > 0">
        <el-table :data="dependencies" border stripe>
          <el-table-column prop="predecessorName" label="依赖任务" min-width="200">
            <template #default="{ row }">
              <div class="task-info">
                <el-link type="primary" @click="viewTask(row.predecessorId)">
                  <strong>{{ row.predecessorName }}</strong>
                </el-link>
                <el-tag size="small" :type="getScenarioColor(row.predecessorScenario)" style="margin-left: 8px">
                  {{ getScenarioLabel(row.predecessorScenario) }}
                </el-tag>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="predecessorScenario" label="场景" width="120">
            <template #default="{ row }">
              {{ getScenarioLabel(row.predecessorScenario) }}
            </template>
          </el-table-column>

          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.satisfied" type="success" size="small">
                已满足
              </el-tag>
              <el-tag v-else type="warning" size="small">
                未满足
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="reason" label="说明" min-width="180">
            <template #default="{ row }">
              <span v-if="row.satisfied" style="color: #67C23A">
                <el-icon><CircleCheck /></el-icon>
                依赖任务执行成功
              </span>
              <span v-else style="color: #E6A23C">
                <el-icon><Warning /></el-icon>
                {{ row.reason || '等待依赖任务完成' }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-popconfirm
                title="确定移除此依赖吗?"
                confirm-button-text="确定"
                cancel-button-text="取消"
                @confirm="handleRemove(row)"
              >
                <template #reference>
                  <el-button link type="danger">
                    <el-icon><Delete /></el-icon>
                    移除
                  </el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <!-- 依赖链预览 -->
        <el-divider content-position="left">执行顺序预览</el-divider>
        <div v-if="dependencyChain.length > 0" class="dependency-chain">
          <div v-for="(task, index) in dependencyChain" :key="task.id" class="chain-item">
            <div class="task-card" :class="{ active: task.id === taskId }">
              <div class="task-order">{{ index + 1 }}</div>
              <div class="task-content">
                <div class="task-name">{{ task.name }}</div>
                <div class="task-meta">
                  <el-tag size="small" :type="getScenarioColor(task.scenario)">
                    {{ getScenarioLabel(task.scenario) }}
                  </el-tag>
                  <el-tag size="small" :type="getStatusType(task.status)">
                    {{ getStatusLabel(task.status) }}
                  </el-tag>
                </div>
              </div>
            </div>
            <el-icon v-if="index < dependencyChain.length - 1" class="chain-arrow">
              <Right />
            </el-icon>
          </div>
        </div>
        <el-empty v-else description="暂无依赖链" />
      </div>

      <el-empty v-else description="暂无依赖任务，点击上方按钮添加">
        <el-button type="primary" @click="showAddDialog = true">
          添加第一个依赖
        </el-button>
      </el-empty>
    </el-card>

    <!-- 添加依赖对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加任务依赖"
      width="600px"
      append-to-body
    >
      <el-form :model="addForm" label-width="100px">
        <el-form-item label="选择任务">
          <el-select
            v-model="addForm.predecessorId"
            filterable
            placeholder="请选择依赖的任务（前置任务）"
            style="width: 100%"
          >
            <el-option
              v-for="task in availableTasks"
              :key="task.id"
              :label="task.name"
              :value="task.id"
              :disabled="task.id === taskId || isDependencyExist(task.id)"
            >
              <div style="display: flex; justify-content: space-between; align-items: center">
                <span>{{ task.name }}</span>
                <div>
                  <el-tag size="small" :type="getScenarioColor(task.scenario)" style="margin-right: 4px">
                    {{ getScenarioLabel(task.scenario) }}
                  </el-tag>
                  <el-tag v-if="task.id === taskId" size="small" type="info">当前任务</el-tag>
                  <el-tag v-else-if="isDependencyExist(task.id)" size="small" type="warning">已添加</el-tag>
                </div>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">
            <el-icon><QuestionFilled /></el-icon>
            所选任务将在当前任务之前执行，当前任务会等待所选任务执行成功后才启动
          </div>
        </el-form-item>

        <el-alert
          title="依赖说明"
          type="info"
          :closable="false"
          show-icon
        >
          <ul style="margin: 8px 0 0 0; padding-left: 20px">
            <li>前置任务执行成功后，当前任务才会自动执行</li>
            <li>如果前置任务执行失败，当前任务将不会执行</li>
            <li>支持多级依赖，系统会自动检测并防止循环依赖</li>
          </ul>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="adding" @click="handleAdd">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Link, Plus, Delete, Right, CircleCheck, Warning, QuestionFilled } from '@element-plus/icons-vue'
import {
  getDependencies,
  addDependency,
  removeDependency,
  getDependencyChain,
  listTasks
} from '@/api/data/etl'

const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['change'])

const dependencies = ref([])
const dependencyChain = ref([])
const availableTasks = ref([])
const showAddDialog = ref(false)
const adding = ref(false)

const addForm = reactive({
  predecessorId: ''
})

// 加载依赖列表
async function loadDependencies() {
  try {
    const res = await getDependencies(props.taskId)
    dependencies.value = res.rows || []
  } catch (error) {
    console.error('获取依赖列表失败:', error)
  }
}

// 加载依赖链
async function loadDependencyChain() {
  try {
    const res = await getDependencyChain(props.taskId)
    dependencyChain.value = res.chain || []
  } catch (error) {
    console.error('获取依赖链失败:', error)
  }
}

// 加载可用任务列表
async function loadAvailableTasks() {
  try {
    const res = await listTasks({ pageNum: 1, pageSize: 1000, status: '0' })
    availableTasks.value = res.rows || []
  } catch (error) {
    console.error('获取任务列表失败:', error)
  }
}

// 添加依赖
async function handleAdd() {
  if (!addForm.predecessorId) {
    return
  }

  adding.value = true
  try {
    await addDependency(props.taskId, { predecessor_id: addForm.predecessorId })
    showAddDialog.value = false
    addForm.predecessorId = ''
    await loadDependencies()
    await loadDependencyChain()
    emit('change')
  } catch (error) {
    console.error('添加依赖失败:', error)
  } finally {
    adding.value = false
  }
}

// 移除依赖
async function handleRemove(row) {
  try {
    await removeDependency(props.taskId, { dependency_id: row.predecessorId })
    await loadDependencies()
    await loadDependencyChain()
    emit('change')
  } catch (error) {
    console.error('移除依赖失败:', error)
  }
}

// 检查依赖是否已存在
function isDependencyExist(predecessorId) {
  return dependencies.value.some(dep => dep.predecessorId === predecessorId)
}

// 查看任务
function viewTask(taskId) {
  // TODO: 跳转到任务详情页
  console.log('查看任务:', taskId)
}

// 获取场景颜色
function getScenarioColor(scenario) {
  const colors = {
    biz_to_stg: '',
    stg_to_ods: 'success',
    warehouse_transform: 'danger',
    warehouse_to_biz: 'warning',
    db_to_db: 'info'
  }
  return colors[scenario] || ''
}

// 获取场景标签
function getScenarioLabel(scenario) {
  const labels = {
    biz_to_stg: '业务库 → STG',
    stg_to_ods: 'STG → ODS',
    warehouse_transform: '数仓计算',
    warehouse_to_biz: '数仓 → 业务库',
    db_to_db: '库库同步'
  }
  return labels[scenario] || scenario
}

// 获取状态类型
function getStatusType(status) {
  const types = {
    '0': 'success',
    '1': 'danger'
  }
  return types[status] || 'info'
}

// 获取状态标签
function getStatusLabel(status) {
  const labels = {
    '0': '正常',
    '1': '停用'
  }
  return labels[status] || status
}

onMounted(() => {
  loadDependencies()
  loadDependencyChain()
  loadAvailableTasks()
})
</script>

<style scoped lang="scss">
.dependency-config {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .header-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }

  .task-info {
    display: flex;
    align-items: center;
  }

  .dependency-chain {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    padding: 16px;
    background-color: #f5f7fa;
    border-radius: 8px;

    .chain-item {
      display: flex;
      align-items: center;
      gap: 8px;

      .task-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background-color: #fff;
        border-radius: 8px;
        border: 2px solid #e4e7ed;
        transition: all 0.3s;

        &.active {
          border-color: #409EFF;
          box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
        }

        .task-order {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background-color: #409EFF;
          color: #fff;
          border-radius: 50%;
          font-weight: 600;
          font-size: 14px;
        }

        .task-content {
          .task-name {
            font-size: 14px;
            font-weight: 500;
            color: #303133;
            margin-bottom: 4px;
          }

          .task-meta {
            display: flex;
            gap: 4px;
          }
        }
      }

      .chain-arrow {
        color: #909399;
        font-size: 20px;
      }
    }
  }

  .form-tip {
    margin-top: 8px;
    font-size: 12px;
    color: #909399;
    display: flex;
    align-items: center;
    gap: 4px;
  }
}
</style>
