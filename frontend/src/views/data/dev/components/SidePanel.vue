<template>
  <div class="side-panel">
    <!-- 数据目录（分层） -->
    <div class="panel-section catalog-section">
      <div class="section-header">
        <span class="section-title">数据目录</span>
        <div class="header-actions">
          <el-button link type="primary" @click="refreshCatalog" :icon="Refresh" title="刷新目录" />
        </div>
      </div>
      <el-input v-model="catalogFilter" placeholder="搜索" size="small" clearable :prefix-icon="Search" class="filter-input" />
      <el-scrollbar class="catalog-scroll">
        <el-tree
          ref="catalogTreeRef"
          :key="catalogKey"
          lazy
          :load="loadCatalogNode"
          :props="catalogTreeProps"
          node-key="id"
          :filter-node-method="filterCatalogNode"
          default-expand-all
          highlight-current
          @node-click="handleCatalogNodeClick"
        >
          <template #default="{ node, data }">
            <span class="tree-node">
              <el-icon v-if="data.type === 'layer'" class="node-icon layer-icon"><FolderOpened /></el-icon>
              <el-icon v-else-if="data.type === 'ds'" class="node-icon ds-icon"><Coin /></el-icon>
              <el-icon v-else class="node-icon table-icon"><Grid /></el-icon>
              <span class="node-label" :title="data.comment ? `${node.label} — ${data.comment}` : node.label">{{ node.label }}</span>
              <span v-if="data.comment" class="node-comment">{{ data.comment }}</span>
              <el-button
                v-if="data.type === 'layer'"
                link type="primary" :icon="Plus" class="node-add-btn"
                :title="`在 ${data.layerKey} 层新建脚本`"
                @click.stop="$emit('create', { type: 'layer', layerKey: data.layerKey })"
              />
              <el-button
                v-if="data.type === 'ds'"
                link type="primary" :icon="Plus" class="node-add-btn"
                title="在此数据源新建脚本"
                @click.stop="$emit('create', { type: 'ds', layerKey: data.layerKey, dsId: data.dsId, dbType: data.dbType })"
              />
            </span>
          </template>
        </el-tree>
      </el-scrollbar>
    </div>

    <!-- 我的脚本 -->
    <div class="panel-section script-section">
      <div class="section-header">
        <span class="section-title">我的脚本</span>
        <el-button link type="primary" @click="$emit('create', null)" :icon="Plus" title="新建脚本" />
      </div>
      <el-input v-model="scriptFilter" placeholder="搜索脚本" size="small" clearable :prefix-icon="Search" class="filter-input" />
      <el-scrollbar class="script-scroll">
        <template v-for="layerItem in layeredScripts" :key="layerItem.key">
          <div v-if="layerItem.scripts.length > 0" class="layer-group">
            <div class="layer-group-title">
              <el-icon class="layer-group-icon"><FolderOpened /></el-icon>
              <span>{{ layerItem.label }}</span>
              <span class="layer-group-count">{{ layerItem.scripts.length }}</span>
            </div>
            <div
              v-for="s in layerItem.scripts"
              :key="s.scriptId"
              class="script-item"
              :class="{ active: s.scriptId === activeScriptId }"
              @click="$emit('select', s)"
            >
              <el-icon class="script-icon"><DataLine /></el-icon>
              <div class="script-info">
                <span class="script-name" :title="s.scriptName">{{ s.scriptName }}</span>
                <span class="script-meta">{{ s.scriptCode }}</span>
              </div>
              <el-tag :type="statusTagType(s.status)" size="small" effect="plain">{{ statusLabel(s.status) }}</el-tag>
            </div>
          </div>
        </template>
        <template v-if="unLayeredScripts.length > 0">
          <div class="layer-group">
            <div class="layer-group-title">
              <el-icon class="layer-group-icon"><Folder /></el-icon>
              <span>未分层</span>
              <span class="layer-group-count">{{ unLayeredScripts.length }}</span>
            </div>
            <div
              v-for="s in unLayeredScripts"
              :key="s.scriptId"
              class="script-item"
              :class="{ active: s.scriptId === activeScriptId }"
              @click="$emit('select', s)"
            >
              <el-icon class="script-icon"><DataLine /></el-icon>
              <div class="script-info">
                <span class="script-name" :title="s.scriptName">{{ s.scriptName }}</span>
                <span class="script-meta">{{ s.scriptCode }}</span>
              </div>
              <el-tag :type="statusTagType(s.status)" size="small" effect="plain">{{ statusLabel(s.status) }}</el-tag>
            </div>
          </div>
        </template>
        <div v-if="filteredScripts.length === 0" class="empty-tip">暂无脚本</div>
      </el-scrollbar>
    </div>
  </div>
</template>

<script setup>
import { Search, Refresh, Plus, Coin, Grid, DataLine, FolderOpened, Folder } from '@element-plus/icons-vue'
import { listDatasource } from '@/api/data/datasource'
import { listMetaTables } from '@/api/data/meta'

defineOptions({ name: 'DevSidePanel' })

const props = defineProps({
  scripts: { type: Array, default: () => [] },
  activeScriptId: { type: Number, default: null },
})

const emit = defineEmits(['select', 'create', 'layer-change'])

// ── 分层配置 ────────────────────────────
const LAYERS = [
  { key: 'ODS', label: 'ODS 贴源层' },
  { key: 'DWD', label: 'DWD 明细层' },
  { key: 'DWS', label: 'DWS 汇总层' },
  { key: 'ADS', label: 'ADS 应用层' },
]

function getDatasourceLayer(dsName) {
  const name = (dsName || '').toUpperCase()
  for (const layer of LAYERS) {
    if (name.startsWith(layer.key)) return layer.key
  }
  return null
}

// ── 数据目录树 ────────────────────────────
const catalogTreeRef = ref(null)
const catalogKey = ref(0)
const catalogFilter = ref('')
const activeLayerFilter = ref('')

async function loadCatalogNode(node, resolve) {
  if (node.level === 0) {
    return resolve(LAYERS.map(l => ({
      id: `layer-${l.key}`,
      label: l.label,
      type: 'layer',
      layerKey: l.key,
      isLeaf: false,
    })))
  }
  if (node.data.type === 'layer') {
    try {
      const res = await listDatasource({ page: 1, pageSize: 999 })
      const all = res.data?.results || res.data || []
      const layerKey = node.data.layerKey
      const matched = all.filter(ds => getDatasourceLayer(ds.dsName) === layerKey)
      return resolve(matched.map(ds => ({
        id: `ds-${ds.dsId}`,
        label: ds.dsName,
        type: 'ds',
        layerKey,
        dsId: ds.dsId,
        dbType: ds.dbType,
        isLeaf: false,
      })))
    } catch {
      return resolve([])
    }
  }
  if (node.data.type === 'ds') {
    try {
      const res = await listMetaTables({ dataSourceId: node.data.dsId, page: 1, pageSize: 999 })
      const tables = res.data?.results || res.data || []
      return resolve(tables.map(t => ({
        id: `tbl-${node.data.dsId}-${t.tableName}`,
        label: t.tableName,
        comment: t.tableComment,
        type: 'table',
        layerKey: node.data.layerKey,
        isLeaf: true,
      })))
    } catch {
      return resolve([])
    }
  }
  resolve([])
}

const catalogTreeProps = { label: 'label', children: 'children', isLeaf: 'isLeaf' }

function filterCatalogNode(value, data) {
  if (!value) return true
  return data.label?.toLowerCase().includes(value.toLowerCase())
}

watch(catalogFilter, val => {
  catalogTreeRef.value?.filter(val)
})

function refreshCatalog() {
  catalogKey.value++
}

function handleCatalogNodeClick(data) {
  const layerKey = data?.layerKey
  if (!layerKey) return
  const next = activeLayerFilter.value === layerKey ? '' : layerKey
  activeLayerFilter.value = next
  emit('layer-change', next)
}

// ── 我的脚本 ────────────────────────────
const scriptFilter = ref('')

const filteredScripts = computed(() => {
  const baseScripts = activeLayerFilter.value
    ? props.scripts.filter(s => s.layer === activeLayerFilter.value)
    : props.scripts
  if (!scriptFilter.value) return baseScripts
  const q = scriptFilter.value.toLowerCase()
  return baseScripts.filter(s => s.scriptName?.toLowerCase().includes(q) || s.scriptCode?.toLowerCase().includes(q))
})

const layeredScripts = computed(() =>
  LAYERS.map(l => ({
    key: l.key,
    label: l.label,
    scripts: filteredScripts.value.filter(s => s.layer === l.key),
  }))
)

const unLayeredScripts = computed(() =>
  filteredScripts.value.filter(s => !s.layer || !LAYERS.some(l => l.key === s.layer))
)

function statusLabel(status) {
  const map = { running: '运行中', success: '成功', failed: '失败', idle: '空闲' }
  return map[status] || status || '未运行'
}
function statusTagType(status) {
  const map = { running: 'warning', success: 'success', failed: 'danger', idle: 'info' }
  return map[status] || 'info'
}
</script>

<style lang="scss" scoped>
.side-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}
.panel-section {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.catalog-section {
  flex: 0 0 50%;
  border-bottom: 1px solid #e4e7ed;
}
.script-section {
  flex: 1;
  min-height: 0;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px 4px;
  .section-title {
    font-size: 13px;
    font-weight: 600;
    color: #303133;
  }
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}
.filter-input {
  margin: 0 8px 6px;
}
.catalog-scroll {
  flex: 1;
  min-height: 0;
  padding: 0 4px;
}
.tree-node {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  overflow: hidden;
  width: 100%;
  .node-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
  }
  .node-comment {
    font-size: 11px;
    color: #909399;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 80px;
    flex-shrink: 0;
  }
  .node-add-btn {
    flex-shrink: 0;
    opacity: 0;
    padding: 0 2px;
    height: auto;
    transition: opacity 0.15s;
  }
  &:hover .node-add-btn {
    opacity: 1;
  }
}
.node-icon  { flex-shrink: 0; }
.layer-icon { color: #e6a23c; }
.ds-icon    { color: #409eff; }
.table-icon { color: #67c23a; }

.script-scroll {
  flex: 1;
  min-height: 0;
  padding: 0 4px;
}
.empty-tip {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 24px 0;
}
.layer-group {
  margin-bottom: 4px;
}
.layer-group-title {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 2px;
}
.layer-group-icon { color: #e6a23c; font-size: 14px; }
.layer-group-count {
  margin-left: auto;
  font-size: 11px;
  color: #909399;
  background: #e4e7ed;
  border-radius: 8px;
  padding: 0 6px;
  line-height: 16px;
}
.script-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px 6px 20px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
  &:hover { background: #f5f7fa; }
  &.active { background: #ecf5ff; }
}
.script-icon {
  flex-shrink: 0;
  font-size: 14px;
  color: #409eff;
}
.script-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.script-name {
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.script-meta {
  font-size: 11px;
  color: #909399;
}
</style>
