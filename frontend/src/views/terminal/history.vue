<template>
  <div class="app-container">
    <el-tabs v-model="activePane" @tab-click="onTabSwitch">
      <!-- ═══ 会话列表 ═══ -->
      <el-tab-pane label="会话记录" name="sessions">
        <!-- 搜索 -->
        <el-form :model="sessionQuery" :inline="true" class="search-form">
          <el-form-item label="状态">
            <el-select v-model="sessionQuery.status" placeholder="全部" clearable style="width: 120px">
              <el-option label="已连接" value="0" />
              <el-option label="已断开" value="1" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="sessionDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 240px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Search" @click="handleSessionQuery">搜索</el-button>
            <el-button icon="Refresh" @click="resetSessionQuery">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- 表格 -->
        <el-table :data="sessionList" v-loading="sessionLoading" stripe>
          <el-table-column prop="sessionId" label="会话 ID" width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="session-id">{{ row.sessionId?.substring(0, 8) }}...</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === '0' ? 'success' : 'info'" size="small">
                {{ row.status === '0' ? '已连接' : '已断开' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="host" label="主机" width="120" />
          <el-table-column prop="userName" label="用户" width="100" />
          <el-table-column prop="commandCount" label="命令数" width="90" align="center">
            <template #default="{ row }">
              <el-tag type="primary" size="small" effect="plain">{{ row.commandCount || 0 }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="时长" width="100" align="center">
            <template #default="{ row }">
              {{ formatDuration(row.duration) }}
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="创建时间" width="180" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="viewSessionCommands(row)">
                查看命令
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <pagination
          v-show="sessionTotal > 0"
          :total="sessionTotal"
          v-model:page="sessionQuery.pageNum"
          v-model:limit="sessionQuery.pageSize"
          @pagination="getSessionList"
        />
      </el-tab-pane>

      <!-- ═══ 命令历史 ═══ -->
      <el-tab-pane label="命令历史" name="commands">
        <!-- 搜索 -->
        <el-form :model="cmdQuery" :inline="true" class="search-form">
          <el-form-item label="关键词">
            <el-input
              v-model="cmdQuery.keyword"
              placeholder="搜索命令..."
              clearable
              style="width: 200px"
              @keyup.enter="handleCmdQuery"
            />
          </el-form-item>
          <el-form-item label="会话 ID">
            <el-input
              v-model="cmdQuery.sessionId"
              placeholder="按会话筛选"
              clearable
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Search" @click="handleCmdQuery">搜索</el-button>
            <el-button icon="Refresh" @click="resetCmdQuery">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- 表格 -->
        <el-table :data="commandList" v-loading="cmdLoading" stripe>
          <el-table-column prop="sessionId" label="会话 ID" width="140" show-overflow-tooltip>
            <template #default="{ row }">
              <el-link type="primary" :underline="false" @click="filterBySession(row.sessionId)">
                {{ row.sessionId?.substring(0, 8) }}...
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="command" label="命令" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <code class="cmd-text">{{ row.command }}</code>
            </template>
          </el-table-column>
          <el-table-column prop="exitCode" label="退出码" width="90" align="center">
            <template #default="{ row }">
              <el-tag
                v-if="row.exitCode !== null && row.exitCode !== undefined"
                :type="row.exitCode === 0 ? 'success' : 'danger'"
                size="small"
                effect="dark"
              >
                {{ row.exitCode }}
              </el-tag>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="executionTime" label="耗时" width="90" align="center">
            <template #default="{ row }">
              {{ row.executionTime != null ? row.executionTime.toFixed(2) + 's' : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="userName" label="用户" width="100" />
          <el-table-column prop="createTime" label="执行时间" width="180" />
        </el-table>
        <pagination
          v-show="cmdTotal > 0"
          :total="cmdTotal"
          v-model:page="cmdQuery.pageNum"
          v-model:limit="cmdQuery.pageSize"
          @pagination="getCommandList"
        />
      </el-tab-pane>
    </el-tabs>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { terminalApi } from '@/api/terminal'

// ── 会话列表 ─────────────────────────────────────────────────────
const sessionQuery = ref({ pageNum: 1, pageSize: 10, status: '', host: '' })
const sessionDateRange = ref(null)
const sessionList = ref([])
const sessionTotal = ref(0)
const sessionLoading = ref(false)

async function getSessionList() {
  sessionLoading.value = true
  try {
    const params = { ...sessionQuery.value }
    if (sessionDateRange.value?.length === 2) {
      params.beginTime = sessionDateRange.value[0]
      params.endTime = sessionDateRange.value[1]
    }
    const res = await terminalApi.listSessions(params)
    sessionList.value = res.rows || []
    sessionTotal.value = res.total || 0
  } catch { ElMessage.error('加载会话列表失败') }
  finally { sessionLoading.value = false }
}

function handleSessionQuery() {
  sessionQuery.value.pageNum = 1
  getSessionList()
}

function resetSessionQuery() {
  sessionQuery.value = { pageNum: 1, pageSize: 10, status: '', host: '' }
  sessionDateRange.value = null
  getSessionList()
}

function viewSessionCommands(row) {
  activePane.value = 'commands'
  cmdQuery.value.sessionId = row.sessionId
  cmdQuery.value.pageNum = 1
  getCommandList()
}

// ── 命令历史 ─────────────────────────────────────────────────────
const cmdQuery = ref({ pageNum: 1, pageSize: 10, keyword: '', sessionId: '' })
const commandList = ref([])
const cmdTotal = ref(0)
const cmdLoading = ref(false)

async function getCommandList() {
  cmdLoading.value = true
  try {
    const res = await terminalApi.getRecentCommands(cmdQuery.value)
    commandList.value = res.rows || []
    cmdTotal.value = res.total || 0
  } catch { ElMessage.error('加载命令历史失败') }
  finally { cmdLoading.value = false }
}

function handleCmdQuery() {
  cmdQuery.value.pageNum = 1
  getCommandList()
}

function resetCmdQuery() {
  cmdQuery.value = { pageNum: 1, pageSize: 10, keyword: '', sessionId: '' }
  getCommandList()
}

function filterBySession(sessionId) {
  cmdQuery.value.sessionId = sessionId
  cmdQuery.value.pageNum = 1
  getCommandList()
}

// ── Tab 切换 & 工具函数 ──────────────────────────────────────────
const activePane = ref('sessions')

function onTabSwitch(tab) {
  if (tab.paneName === 'sessions' && sessionList.value.length === 0) getSessionList()
  if (tab.paneName === 'commands' && commandList.value.length === 0) getCommandList()
}

function formatDuration(seconds) {
  if (seconds == null) return '-'
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

// ── 生命周期 ─────────────────────────────────────────────────────
onMounted(() => getSessionList())
</script>

<style scoped>
.search-form {
  margin-bottom: 16px;
}

.session-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #606266;
}

.cmd-text {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  color: #303133;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
}

.text-muted {
  color: #c0c4cc;
}

</style>
