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
          :data="catalogTreeData"
          :props="catalogTreeProps"
          node-key="id"
          :filter-node-method="filterCatalogNode"
          :default-expanded-keys="defaultExpandedKeys"
          highlight-current
          :render-after-expand="false"
          :expand-on-click-node="false"
          @node-click="handleCatalogNodeClick"
        >
          <template #default="{ node, data }">
            <span class="tree-node" @click="handleCatalogNodeClick(data)">
              <el-icon v-if="data.type === 'directory' || data.type === 'default-directory'" class="node-icon layer-icon"><FolderOpened /></el-icon>
              <el-icon v-else class="node-icon table-icon"><DataLine /></el-icon>
              <span class="node-label" :title="data.comment ? `${node.label} — ${data.comment}` : node.label">
                {{ node.label }}
                <span v-if="data.childCount != null" class="node-count">{{ data.childCount }}</span>
              </span>
              <!-- <span v-if="data.comment" class="node-comment">{{ data.comment }}</span> -->
              <el-button
                v-if="data.type === 'directory' || data.type === 'default-directory'"
                link type="primary" :icon="Plus" class="node-add-btn"
                :title="`在 ${data.label} 新建脚本`"
                @click.stop="$emit('create', { type: 'directory', directoryId: data.directoryId, directoryCode: data.directoryCode })"
              />
            </span>
          </template>
        </el-tree>
      </el-scrollbar>
    </div>

  </div>
</template>

<script setup>
import { Search, Refresh, Plus, DataLine, FolderOpened } from '@element-plus/icons-vue'

defineOptions({ name: 'DevSidePanel' })

const props = defineProps({
  scripts: { type: Array, default: () => [] },
  activeScriptId: { type: Number, default: null },
  directories: { type: Array, default: () => [] },
  activeDirectoryId: { type: Number, default: null },
})

const emit = defineEmits(['select', 'create', 'directory-change', 'refresh'])

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

const unassignedScripts = computed(() =>
  props.scripts.filter(s => !s.directoryId || !flatDirectories.value.some(d => d.directoryId === s.directoryId))
)

function mapScriptNode(script, parentDirectoryId) {
  return {
    id: `script-${script.scriptId}`,
    label: script.scriptName,
    type: 'script',
    comment: script.description || '',
    script,
    directoryId: parentDirectoryId,
    isLeaf: true,
  }
}

function buildCatalogDirectoryNode(directory) {
  const childDirectoryNodes = (directory.children || []).map(buildCatalogDirectoryNode)
  const directoryScripts = props.scripts
    .filter(script => script.directoryId === directory.directoryId)
    .map(script => mapScriptNode(script, directory.directoryId))

  // 保证 children 至少为 []，isLeaf 始终为 false
  const allChildren = [...childDirectoryNodes, ...directoryScripts]
  return {
    id: `directory-${directory.directoryId}`,
    label: directory.directoryName,
    type: 'directory',
    comment: directory.remark || '',
    childCount: allChildren.length,
    directoryId: directory.directoryId,
    directoryCode: directory.directoryCode,
    isLeaf: false,
    children: allChildren.length ? allChildren : [],
  }
}

const catalogTreeData = computed(() => {
  const directoryNodes = (props.directories || []).map(buildCatalogDirectoryNode)
  const defaultChildren = unassignedScripts.value.map(script => mapScriptNode(script, null))
  const defaultDirectoryNode = {
    id: 'directory-default',
    label: '未分配目录',
    type: 'default-directory',
    childCount: defaultChildren.length,
    directoryId: null,
    isLeaf: false,
    children: defaultChildren.length ? defaultChildren : [],
  }
  return [...directoryNodes, defaultDirectoryNode]
})

const defaultExpandedKeys = computed(() =>
  catalogTreeData.value
    .filter(n => n.type === 'directory' || n.type === 'default-directory')
    .map(n => n.id)
)

// ── 数据目录树 ────────────────────────────
const catalogTreeRef = ref(null)
const catalogKey = ref(0)
const catalogFilter = ref('')

watch(
  () => props.activeDirectoryId,
  (directoryId) => {
    nextTick(() => {
      catalogTreeRef.value?.setCurrentKey(
        directoryId ? `directory-${directoryId}` : null,
        true,
      )
    })
  },
  { immediate: true }
)

watch(
  () => props.activeScriptId,
  (scriptId) => {
    if (!scriptId) return
    nextTick(() => {
      catalogTreeRef.value?.setCurrentKey(`script-${scriptId}`, true)
    })
  },
  { immediate: true }
)

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
  emit('refresh')
}

function handleCatalogNodeClick(data) {
  // 只选中节点，不自动展开所有父节点
  if (data?.id) {
    catalogTreeRef.value?.setCurrentKey(data.id)
  }
  if (data?.type === 'script') {
    emit('select', data.script)
    return
  }
  if (data?.type === 'directory') {
    const next = props.activeDirectoryId === data.directoryId ? null : data.directoryId
    emit('directory-change', next)
    return
  }
  if (data?.type === 'default-directory') {
    emit('directory-change', null)
  }
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
  font-size: 13px;
  overflow: hidden;
  width: 100%;
  gap: 4px;
  .node-label {
    display: inline-flex;
    align-items: center;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
    /* 不再 flex:1，防止数量被推远 */
  }
  .node-count {
    font-size: 11px;
    color: var(--panel-sub);
    background: #f0f2f5;
    border-radius: 8px;
    padding: 0 5px;
    line-height: 16px;
    margin-left: 2px;
    flex-shrink: 0;
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
.table-icon { color: var(--panel-accent); }

@media (max-width: 768px) {
  .section-header {
    padding: 6px 10px 4px;
  }
  .filter-input {
    margin: 0 6px 5px;
  }
}
</style>
