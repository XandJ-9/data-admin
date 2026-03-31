<template>
  <div class="history-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>Terminal Command History</span>
        </div>
      </template>

      <!-- Search Form -->
      <el-form :model="queryParams" ref="queryRef" :inline="true" class="search-form">
        <el-form-item label="Keyword" prop="keyword">
          <el-input v-model="queryParams.keyword" placeholder="Search command..." />
        </el-form-item>
        <el-form-item label="Session ID" prop="sessionId">
          <el-input v-model="queryParams.sessionId" placeholder="Filter by session..." />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">Search</el-button>
          <el-button @click="resetQuery">Reset</el-button>
        </el-form-item>
      </el-form>

      <!-- Command Table -->
      <el-table :data="commandList" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="sessionId" label="Session ID" width="200" />
        <el-table-column prop="command" label="Command" show-overflow-tooltip />
        <el-table-column prop="exitCode" label="Exit Code" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.exitCode === 0 ? 'success' : 'danger'"
              v-if="row.exitCode !== null"
            >
              {{ row.exitCode }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="executionTime" label="Time (s)" width="100" />
        <el-table-column prop="userName" label="User" width="100" />
        <el-table-column prop="createTime" label="Created At" width="180" />
        <el-table-column label="Actions" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleViewOutput(row)"
            >
              Output
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <pagination
        v-show="total > 0"
        :total="total"
        v-model:page="queryParams.pageNum"
        v-model:limit="queryParams.pageSize"
        @pagination="getList"
      />
    </el-card>

    <!-- Output Dialog -->
    <el-dialog v-model="outputDialogVisible" title="Command Output" width="800px">
      <div class="output-content">
        <pre>{{ currentCommand?.output }}</pre>
      </div>
      <template #footer>
        <el-button @click="outputDialogVisible = false">Close</el-button>
        <el-button type="primary" @click="copyOutput">Copy</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import terminalApi from '@/api/terminal'

// State
const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  keyword: '',
  sessionId: ''
})

const commandList = ref([])
const total = ref(0)
const loading = ref(false)
const outputDialogVisible = ref(false)
const currentCommand = ref(null)
const queryRef = ref(null)

/**
 * Get command history
 */
const getList = async () => {
  loading.value = true
  try {
    const params = {
      pageNum: queryParams.value.pageNum,
      pageSize: queryParams.value.pageSize
    }

    // Use search API if keyword provided
    if (queryParams.value.keyword) {
      const res = await terminalApi.searchCommands(queryParams.value.keyword, params)
      commandList.value = res.rows || []
      total.value = res.total || 0
    } else {
      // Otherwise get recent commands
      const res = await terminalApi.getRecentCommands(params)
      commandList.value = res.rows || []
      total.value = res.total || 0
    }
  } catch (error) {
    ElMessage.error('Failed to load commands: ' + error.message)
  } finally {
    loading.value = false
  }
}

/**
 * Handle search
 */
const handleQuery = () => {
  queryParams.value.pageNum = 1
  getList()
}

/**
 * Reset search
 */
const resetQuery = () => {
  queryParams.value = {
    pageNum: 1,
    pageSize: 10,
    keyword: '',
    sessionId: ''
  }
  getList()
}

/**
 * View command output
 */
const handleViewOutput = (row) => {
  currentCommand.value = row
  outputDialogVisible.value = true
}

/**
 * Copy output to clipboard
 */
const copyOutput = async () => {
  if (!currentCommand.value?.output) return

  try {
    await navigator.clipboard.writeText(currentCommand.value.output)
    ElMessage.success('Output copied to clipboard')
  } catch (error) {
    ElMessage.error('Failed to copy: ' + error.message)
  }
}

/**
 * Lifecycle
 */
onMounted(() => {
  getList()
})
</script>

<style scoped>
.history-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.output-content {
  background-color: #1e1e1e;
  padding: 16px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
}

.output-content pre {
  color: #d4d4d4;
  font-family: 'Courier New', Courier, monospace;
  font-size: 12px;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
