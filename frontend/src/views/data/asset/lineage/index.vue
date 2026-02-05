<template>
  <div class="app-container">
    <!-- 工具栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="Plus"
          @click="handleAdd"
        >新增血缘</el-button>
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
      <el-col :span="1.5">
        <el-button
          type="info"
          plain
          icon="Share"
          @click="showGraphDialog = true"
        >血缘图</el-button>
      </el-col>
      <right-toolbar
        v-model:showSearch="showSearch"
        @queryTable="getList"
      />
    </el-row>

    <!-- 搜索表单 -->
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="源表" prop="sourceTableName">
        <el-input
          v-model="queryParams.sourceTableName"
          placeholder="请输入源表名"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="目标表" prop="targetTableName">
        <el-input
          v-model="queryParams.targetTableName"
          placeholder="请输入目标表名"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="血缘类型" prop="lineageType">
        <el-select v-model="queryParams.lineageType" placeholder="请选择血缘类型" clearable style="width: 150px">
          <el-option label="上游" value="upstream" />
          <el-option label="下游" value="downstream" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="dataList"
      @selection-change="handleSelectionChange"
      border
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="ID" align="center" prop="id" width="80" />
      <el-table-column label="源表" align="center" prop="sourceTableName" min-width="150" show-overflow-tooltip />
      <el-table-column label="目标表" align="center" prop="targetTableName" min-width="150" show-overflow-tooltip />
      <el-table-column label="血缘类型" align="center" prop="lineageType" width="100">
        <template #default="scope">
          <el-tag v-if="scope.row.lineageType === 'upstream'" type="success">上游</el-tag>
          <el-tag v-else type="info">下游</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="描述" align="center" prop="description" min-width="200" show-overflow-tooltip />
      <el-table-column label="创建时间" align="center" prop="createTime" width="180" />
      <el-table-column label="操作" align="center" width="200" fixed="right">
        <template #default="scope">
          <el-button
            link
            type="primary"
            icon="View"
            @click="handleView(scope.row)"
          >查看</el-button>
          <el-button
            link
            type="primary"
            icon="Edit"
            @click="handleUpdate(scope.row)"
          >修改</el-button>
          <el-button
            link
            type="danger"
            icon="Delete"
            @click="handleDelete(scope.row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 添加/修改对话框 -->
    <el-dialog :title="title" v-model="open" width="600px" append-to-body>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="源表" prop="sourceTableId">
          <el-select
            v-model="form.sourceTableId"
            placeholder="请选择源表"
            filterable
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="table in tableOptions"
              :key="table.id"
              :label="`${table.tableName} (${table.databaseName || '-'})`"
              :value="table.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标表" prop="targetTableId">
          <el-select
            v-model="form.targetTableId"
            placeholder="请选择目标表"
            filterable
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="table in tableOptions"
              :key="table.id"
              :label="`${table.tableName} (${table.databaseName || '-'})`"
              :value="table.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="血缘类型" prop="lineageType">
          <el-radio-group v-model="form.lineageType">
            <el-radio label="upstream">上游</el-radio>
            <el-radio label="downstream">下游</el-radio>
          </el-radio-group>
          <div class="form-item-tip">
            上游：数据来源表，下游：数据目标表
          </div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="请输入描述"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancel">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 血缘图对话框 -->
    <el-dialog title="血缘关系图" v-model="showGraphDialog" width="90%" top="5vh" append-to-body>
      <div class="graph-container">
        <el-form :inline="true" class="graph-form">
          <el-form-item label="查询表">
            <el-select
              v-model="graphQuery.tableId"
              placeholder="请选择表"
              filterable
              clearable
              style="width: 250px"
              @change="loadLineageGraph"
            >
              <el-option
                v-for="table in tableOptions"
                :key="table.id"
                :label="`${table.tableName} (${table.databaseName || '-'})`"
                :value="table.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="查询深度">
            <el-input-number v-model="graphQuery.depth" :min="1" :max="5" controls-position="right" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Refresh" @click="loadLineageGraph">刷新</el-button>
          </el-form-item>
        </el-form>

        <div v-loading="graphLoading" class="graph-canvas">
          <div v-if="graphData.nodes && graphData.nodes.length > 0" class="graph-content">
            <div class="graph-legend">
              <el-tag type="primary">节点: {{ graphData.nodes.length }}</el-tag>
              <el-tag type="success">关系: {{ graphData.edges.length }}</el-tag>
            </div>

            <div class="graph-nodes">
              <div
                v-for="node in graphData.nodes"
                :key="node.id"
                class="graph-node-card"
              >
                <div class="node-header">
                  <el-icon><Grid /></el-icon>
                  <span class="node-title">{{ node.tableName }}</span>
                </div>
                <div class="node-info">
                  <div><span class="label">数据库:</span> {{ node.databaseName || '-' }}</div>
                  <div><span class="label">数据源ID:</span> {{ node.dataSourceId }}</div>
                  <div v-if="node.comment" class="comment">{{ node.comment }}</div>
                </div>
              </div>
            </div>

            <div class="graph-edges">
              <h4>血缘关系</h4>
              <div
                v-for="(edge, index) in graphData.edges"
                :key="index"
                class="graph-edge-item"
              >
                <el-tag :type="edge.type === 'upstream' ? 'success' : 'info'" size="small">
                  {{ edge.type === 'upstream' ? '↑ 上游' : '↓ 下游' }}
                </el-tag>
                <span class="edge-text">
                  {{ getTableName(edge.source) }} → {{ getTableName(edge.target) }}
                </span>
                <span v-if="edge.description" class="edge-desc">({{ edge.description }})</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无血缘数据，请选择表进行查询" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup name="TableLineage">
import {
  listTableLineage,
  getTableLineage,
  addTableLineage,
  updateTableLineage,
  delTableLineage,
  getLineageGraph
} from '@/api/data/asset'
import { listMetaTables } from '@/api/data/asset'
import { Plus, Delete, Search, Refresh, Edit, View, Grid, Share } from '@element-plus/icons-vue'

const { proxy } = getCurrentInstance()

const dataList = ref([])
const open = ref(false)
const showSearch = ref(true)
const showGraphDialog = ref(false)
const title = ref('')
const loading = ref(false)
const graphLoading = ref(false)
const total = ref(0)
const ids = ref([])
const single = ref(true)
const multiple = ref(true)
const tableOptions = ref([])
const graphData = ref({ nodes: [], edges: [] })

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  sourceTableName: null,
  targetTableName: null,
  lineageType: null
})

const graphQuery = ref({
  tableId: null,
  depth: 2
})

const form = ref({})
const rules = ref({
  sourceTableId: [
    { required: true, message: '源表不能为空', trigger: 'change' }
  ],
  targetTableId: [
    { required: true, message: '目标表不能为空', trigger: 'change' }
  ],
  lineageType: [
    { required: true, message: '血缘类型不能为空', trigger: 'change' }
  ]
})

/** 查询表血缘列表 */
function getList() {
  loading.value = true
  listTableLineage(queryParams.value).then(response => {
    dataList.value = response.rows
    total.value = response.total
    loading.value = false
  }).catch(() => {
    loading.value = false
  })
}

/** 取消按钮 */
function cancel() {
  open.value = false
  reset()
}

/** 表单重置 */
function reset() {
  form.value = {
    id: null,
    sourceTableId: null,
    targetTableId: null,
    lineageType: 'upstream',
    description: null
  }
  proxy.resetForm('formRef')
}

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.id)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

/** 新增按钮操作 */
function handleAdd() {
  reset()
  loadTableOptions()
  open.value = true
  title.value = '添加表血缘'
}

/** 修改按钮操作 */
function handleUpdate(row) {
  reset()
  loadTableOptions()
  const id = row.id || ids.value[0]
  getTableLineage(id).then(response => {
    form.value = response.data
    open.value = true
    title.value = '修改表血缘'
  })
}

/** 查看按钮操作 */
function handleView(row) {
  reset()
  const id = row.id
  getTableLineage(id).then(response => {
    form.value = response.data
    open.value = true
    title.value = '查看表血缘'
  })
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs.formRef.validate(valid => {
    if (valid) {
      if (form.value.sourceTableId === form.value.targetTableId) {
        proxy.$modal.msgWarning('源表和目标表不能相同')
        return
      }

      if (form.value.id) {
        updateTableLineage(form.value).then(response => {
          proxy.$modal.msgSuccess('修改成功')
          open.value = false
          getList()
        })
      } else {
        addTableLineage(form.value).then(response => {
          proxy.$modal.msgSuccess('新增成功')
          open.value = false
          getList()
        })
      }
    }
  })
}

/** 删除按钮操作 */
function handleDelete(row) {
  const deleteIds = row.id || ids.value.join(',')
  proxy.$modal.confirm('是否确认删除选中的数据项？').then(() => {
    return delTableLineage(deleteIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

/** 加载表选项 */
function loadTableOptions() {
  if (tableOptions.value.length > 0) return

  listMetaTables({ pageNum: 1, pageSize: 10000 }).then(response => {
    tableOptions.value = response.rows
  })
}

/** 加载血缘图 */
function loadLineageGraph() {
  if (!graphQuery.value.tableId) {
    graphData.value = { nodes: [], edges: [] }
    return
  }

  graphLoading.value = true
  getLineageGraph({
    tableId: graphQuery.value.tableId,
    depth: graphQuery.value.depth
  }).then(response => {
    graphData.value = response.data
    graphLoading.value = false
  }).catch(() => {
    graphLoading.value = false
  })
}

/** 获取表名 */
function getTableName(tableId) {
  const node = graphData.value.nodes.find(n => n.id === tableId)
  return node ? node.tableName : tableId
}

// 初始化
getList()
</script>

<style scoped lang="scss">
.form-item-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.graph-container {
  .graph-form {
    margin-bottom: 20px;
    padding: 15px;
    background-color: #f5f7fa;
    border-radius: 4px;
  }

  .graph-canvas {
    min-height: 400px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    padding: 20px;
  }

  .graph-content {
    .graph-legend {
      margin-bottom: 20px;
      display: flex;
      gap: 10px;
    }

    .graph-nodes {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 15px;
      margin-bottom: 30px;
    }

    .graph-node-card {
      padding: 12px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 8px;
      color: white;

      .node-header {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        font-size: 14px;
        font-weight: bold;
      }

      .node-title {
        margin-left: 6px;
      }

      .node-info {
        font-size: 12px;
        opacity: 0.9;

        div {
          margin: 2px 0;
        }

        .label {
          opacity: 0.7;
        }

        .comment {
          margin-top: 6px;
          padding-top: 6px;
          border-top: 1px solid rgba(255, 255, 255, 0.3);
          font-style: italic;
        }
      }
    }

    .graph-edges {
      border-top: 1px solid #dcdfe6;
      padding-top: 20px;

      h4 {
        margin: 0 0 15px 0;
        color: #303133;
      }

      .graph-edge-item {
        padding: 10px 12px;
        background-color: #f5f7fa;
        border-radius: 4px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 14px;

        .edge-text {
          flex: 1;
          color: #606266;
        }

        .edge-desc {
          color: #909399;
          font-size: 12px;
        }
      }
    }
  }
}
</style>
