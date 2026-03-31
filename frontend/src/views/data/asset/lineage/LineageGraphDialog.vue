<template>
  <el-dialog title="血缘关系图" v-model="dialogVisible" width="90%" top="5vh" append-to-body>
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
            <div v-for="node in graphData.nodes" :key="node.id" class="graph-node-card">
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
</template>

<script setup>
import { getLineageGraph } from '@/api/data/asset'
import { Grid } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: Boolean,
  tableOptions: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const graphLoading = ref(false)
const graphData = ref({ nodes: [], edges: [] })
const graphQuery = ref({ tableId: null, depth: 2 })

function loadLineageGraph() {
  if (!graphQuery.value.tableId) {
    graphData.value = { nodes: [], edges: [] }
    return
  }
  graphLoading.value = true
  getLineageGraph({ tableId: graphQuery.value.tableId, depth: graphQuery.value.depth })
    .then(response => { graphData.value = response.data })
    .catch(() => {})
    .finally(() => { graphLoading.value = false })
}

function getTableName(tableId) {
  const node = graphData.value.nodes.find(n => n.id === tableId)
  return node ? node.tableName : tableId
}
</script>

<style scoped lang="scss">
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

      .node-title { margin-left: 6px; }

      .node-info {
        font-size: 12px;
        opacity: 0.9;

        div { margin-bottom: 4px; }
        .label { opacity: 0.7; }
      }
    }

    .graph-edges {
      h4 { margin-bottom: 12px; }

      .graph-edge-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;

        .edge-text { font-size: 14px; }
        .edge-desc { color: #909399; font-size: 12px; }
      }
    }
  }
}
</style>
