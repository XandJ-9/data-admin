<template>
  <div class="side-panel">
    <!-- 数据目录 -->
    <div class="panel-section catalog-section">
      <div class="section-header">
        <span class="section-title">资源导航树</span>
        <div class="header-actions">
          <el-button link type="primary" @click="refreshCatalog" :icon="Refresh" title="刷新目录" />
        </div>
      </div>
      <el-input v-model="catalogFilter" placeholder="快速定位脚本名称" size="small" clearable :prefix-icon="Search" class="filter-input" />
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
              <el-icon v-if="data.type === 'directory'" class="node-icon layer-icon"><FolderOpened /></el-icon>
              <el-icon v-else-if="data.type === 'ds'" class="node-icon ds-icon"><Coin /></el-icon>
              <el-icon v-else class="node-icon table-icon"><Grid /></el-icon>
              <span class="node-label" :title="data.comment ? `${node.label} — ${data.comment}` : node.label">{{ node.label }}</span>
              <span v-if="data.comment" class="node-comment">{{ data.comment }}</span>
              <el-button
                v-if="data.type === 'directory'"
                link type="primary" :icon="Plus" class="node-add-btn"
                :title="`在 ${data.label} 新建脚本`"
                @click.stop="$emit('create', { type: 'directory', directoryId: data.directoryId, directoryCode: data.directoryCode })"
              />
              <el-button
                v-if="data.type === 'ds'"
                link type="primary" :icon="Plus" class="node-add-btn"
                title="在此数据源新建脚本"
                @click.stop="$emit('create', { type: 'ds', directoryId: data.directoryId, dsId: data.dsId, dbType: data.dbType })"
              />
            </span>
          </template>
        </el-tree>
      </el-scrollbar>
    </div>

    <!-- 我的脚本 -->
    <div class="panel-section script-section">
      <div class="section-header">
        <span class="section-title">脚本资源</span>
        <el-button link type="primary" @click="$emit('create', null)" :icon="Plus" title="新建脚本" />
      </div>
      <el-input v-model="scriptFilter" placeholder="搜索脚本" size="small" clearable :prefix-icon="Search" class="filter-input" />
      <el-scrollbar class="script-scroll">
        <template v-for="directoryGroup in groupedScripts" :key="directoryGroup.key">
          <div v-if="directoryGroup.scripts.length > 0" class="layer-group">
            <div class="layer-group-title">
              <el-icon class="layer-group-icon"><FolderOpened /></el-icon>
              <span>{{ directoryGroup.label }}</span>
              <span class="layer-group-count">{{ directoryGroup.scripts.length }}</span>
            </div>
            <div
              v-for="s in directoryGroup.scripts"
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
  directories: { type: Array, default: () => [] },
  activeDirectoryId: { type: Number, default: null },
})

const emit = defineEmits(['select', 'create', 'directory-change'])

function flattenDirectories(nodes) {
  const rows = []
  const walk = (items) => {
    ;(items || []).forEach((item) => {
      rows.push(item)
      if (item.children?.length) {
        walk(item.children)
      }
    })
  }
  walk(nodes)
  return rows
}

const flatDirectories = computed(() => flattenDirectories(props.directories || []))

function mapDirectoryNode(directory) {
  return {
    id: `directory-${directory.directoryId}`,
    label: directory.directoryName,
    type: 'directory',
    directoryId: directory.directoryId,
    directoryCode: directory.directoryCode,
    hasDirectoryChildren: Boolean(directory.children?.length),
    isLeaf: false,
  }
}

function getDatasourceDirectoryCode(dsName) {
  const name = (dsName || '').toUpperCase()
  const sortedDirectories = [...flatDirectories.value].sort(
    (a, b) => String(b.directoryCode || '').length - String(a.directoryCode || '').length,
  )
  for (const directory of sortedDirectories) {
    const code = String(directory.directoryCode || '').toUpperCase()
    if (!code) {
      continue
    }
    if (name === code || name.startsWith(`${code}_`)) {
      return code
    }
  }
  return null
}

async function fetchAllDatasources() {
  const pageSize = 100
  let page = 1
  let allRows = []

  while (true) {
    const res = await listDatasource({ page, pageSize })
    const rows = res.data?.results || res.data || []
    allRows = allRows.concat(rows)
    if (rows.length < pageSize) {
      break
    }
    page += 1
  }

  return allRows
}

// ── 数据目录树 ────────────────────────────
const catalogTreeRef = ref(null)
const catalogKey = ref(0)
const catalogFilter = ref('')
const activeDirectoryFilter = ref(null)

watch(
  () => props.activeDirectoryId,
  (directoryId) => {
    activeDirectoryFilter.value = directoryId || null
    nextTick(() => {
      catalogTreeRef.value?.setCurrentKey(
        directoryId ? `directory-${directoryId}` : null,
        true,
      )
    })
  },
  { immediate: true }
)

async function loadCatalogNode(node, resolve) {
  if (node.level === 0) {
    return resolve((props.directories || []).map(mapDirectoryNode))
  }
  if (node.data.type === 'directory') {
    const currentDirectory = flatDirectories.value.find(
      (directory) => directory.directoryId === node.data.directoryId,
    )
    if (currentDirectory?.children?.length) {
      return resolve(currentDirectory.children.map(mapDirectoryNode))
    }
    try {
      const all = await fetchAllDatasources()
      const directoryCode = node.data.directoryCode
      const matched = all.filter(ds => getDatasourceDirectoryCode(ds.dsName) === directoryCode)
      return resolve(matched.map(ds => ({
        id: `ds-${ds.dsId}`,
        label: ds.dsName,
        type: 'ds',
        directoryId: node.data.directoryId,
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
        directoryId: node.data.directoryId,
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
  if (data?.type !== 'directory') return
  const next = activeDirectoryFilter.value === data.directoryId ? null : data.directoryId
  activeDirectoryFilter.value = next
  emit('directory-change', next)
}

// ── 我的脚本 ────────────────────────────
const scriptFilter = ref('')

const filteredScripts = computed(() => {
  const baseScripts = activeDirectoryFilter.value
    ? props.scripts.filter(s => s.directoryId === activeDirectoryFilter.value)
    : props.scripts
  if (!scriptFilter.value) return baseScripts
  const q = scriptFilter.value.toLowerCase()
  return baseScripts.filter(s => s.scriptName?.toLowerCase().includes(q) || s.scriptCode?.toLowerCase().includes(q))
})

const groupedScripts = computed(() =>
  flatDirectories.value.map((directory) => ({
    key: directory.directoryId,
    label: directory.directoryName,
    scripts: filteredScripts.value.filter(s => s.directoryId === directory.directoryId),
  }))
)

const unLayeredScripts = computed(() =>
  filteredScripts.value.filter(s => !s.directoryId || !flatDirectories.value.some(d => d.directoryId === s.directoryId))
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
  --panel-title: #1f2f45;
  --panel-sub: #5f7188;
  --panel-accent: #1f8f7a;

  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(180deg, #fcfdfd 0%, #f6f9fc 100%);
}
.panel-section {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.catalog-section {
  flex: 0 0 50%;
  border-bottom: 1px solid #dce4ee;
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
    font-weight: 700;
    color: var(--panel-title);
    letter-spacing: 0.2px;
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
    color: var(--panel-sub);
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
.ds-icon    { color: #2f8bc4; }
.table-icon { color: var(--panel-accent); }

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
  color: #46607e;
  background: #edf3f9;
  border: 1px solid #dde7f1;
  border-radius: 8px;
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
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  &:hover { background: #eef6f4; }
  &.active {
    background: #e5f6f1;
    box-shadow: inset 0 0 0 1px #b9e6d9;
  }
}
.script-icon {
  flex-shrink: 0;
  font-size: 14px;
  color: var(--panel-accent);
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
  color: var(--panel-sub);
}

@media (max-width: 768px) {
  .section-header {
    padding: 6px 10px 4px;
  }
  .filter-input {
    margin: 0 6px 5px;
  }
}
</style>
