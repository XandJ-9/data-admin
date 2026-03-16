<template>
  <div class="field-mapping-editor">
    <!-- 字段映射表格 -->
    <el-table
      :data="mappingList"
      border
      stripe
      max-height="500"
      :row-class-name="getRowClassName"
    >
      <el-table-column type="index" label="#" width="50" align="center" />

      <el-table-column label="源字段" width="200">
        <template #default="{ row }">
          <el-select
            v-model="row.source"
            filterable
            placeholder="选择源字段"
            :disabled="disabled"
            @change="handleSourceChange(row)"
          >
            <el-option
              v-for="col in sourceColumns"
              :key="col"
              :label="col"
              :value="col"
              :disabled="isSourceMapped(col, row)"
            />
          </el-select>
        </template>
      </el-table-column>

      <el-table-column label="目标字段" width="200">
        <template #default="{ row }">
          <el-select
            v-model="row.target"
            filterable
            allow-create
            placeholder="选择或输入目标字段"
            :disabled="disabled"
            @change="handleTargetChange(row)"
          >
            <el-option
              v-for="col in targetColumns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </template>
      </el-table-column>

      <el-table-column label="转换规则" min-width="250">
        <template #default="{ row }">
          <el-input
            v-model="row.transform"
            placeholder="可选：输入转换表达式"
            :disabled="disabled || !row.source"
            clearable
          >
            <template #prepend>
              <el-dropdown @command="(cmd) => handleInsertTransform(row, cmd)">
                <span class="transform-btn">
                  常用转换 <el-icon><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="UPPER(${row.source})">转大写</el-dropdown-item>
                    <el-dropdown-item command="LOWER(${row.source})">转小写</el-dropdown-item>
                    <el-dropdown-item command="TRIM(${row.source})">去空格</el-dropdown-item>
                    <el-dropdown-item command="CAST(${row.source} AS STRING)">转字符串</el-dropdown-item>
                    <el-dropdown-item command="CAST(${row.source} AS INT)">转整数</el-dropdown-item>
                    <el-dropdown-item command="CAST(${row.source} AS DECIMAL(10,2))">转小数</el-dropdown-item>
                    <el-dropdown-item command="DATE_FORMAT(${row.source}, 'yyyy-MM-dd')">日期格式化</el-dropdown-item>
                    <el-dropdown-item command="NVL(${row.source}, '')">空值处理</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-input>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" align="center" fixed="right">
        <template #default="{ $index }">
          <el-button
            type="danger"
            size="small"
            :icon="Delete"
            :disabled="disabled"
            @click="handleRemoveMapping($index)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 操作按钮 -->
    <div class="mapping-actions">
      <el-button :icon="Plus" type="primary" :disabled="disabled" @click="handleAddMapping">
        添加映射
      </el-button>
      <el-button :icon="MagicStick" :disabled="disabled" @click="autoMap">
        智能映射
      </el-button>
      <el-button :icon="Delete" :disabled="disabled" @click="clearMappings">
        清空映射
      </el-button>
      <div class="mapping-stats">
        <el-tag size="small" type="info">已映射 {{ mappingList.length }} 对字段</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Plus, Delete, MagicStick, ArrowDown } from '@element-plus/icons-vue'

const props = defineProps({
  sourceColumns: {
    type: Array,
    default: () => []
  },
  targetColumns: {
    type: Array,
    default: () => []
  },
  mappings: {
    type: Array,
    default: () => []
  },
  autoMatch: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:mappings', 'update:sourceColumns', 'update:targetColumns'])

// 映射列表
const mappingList = ref([...props.mappings])

// 监听mappings变化
watch(() => props.mappings, (newVal) => {
  mappingList.value = [...newVal]
}, { deep: true })

// 监听映射列表变化
watch(mappingList, (newVal) => {
  emit('update:mappings', newVal)
}, { deep: true })

// 自动映射
watch(() => props.autoMatch, (newVal) => {
  if (newVal) {
    autoMap()
  }
})

// 获取表格行类名
function getRowClassName({ rowIndex }) {
  return `mapping-row-${rowIndex}`
}

// 检查源字段是否已被映射
function isSourceMapped(source, currentRow) {
  return mappingList.value.some(row => row !== currentRow && row.source === source)
}

// 添加映射
function handleAddMapping() {
  mappingList.value.push({
    source: '',
    target: '',
    transform: ''
  })
}

// 删除映射
function handleRemoveMapping(index) {
  mappingList.value.splice(index, 1)
}

// 清空映射
function clearMappings() {
  mappingList.value = []
}

// 智能映射
function autoMap() {
  const mappings = []
  const sourceMapping = new Map()

  // 创建源字段的映射（忽略大小写）
  props.sourceColumns.forEach(col => {
    sourceMapping.set(col.toLowerCase(), col)
  })

  // 精确匹配
  props.targetColumns.forEach(targetCol => {
    const targetLower = targetCol.toLowerCase()
    if (sourceMapping.has(targetLower)) {
      mappings.push({
        source: sourceMapping.get(targetLower),
        target: targetCol,
        transform: ''
      })
    }
  })

  // 模糊匹配
  props.targetColumns.forEach(targetCol => {
    const targetLower = targetCol.toLowerCase()
    // 跳过已经精确匹配的
    if (mappings.some(m => m.target === targetCol)) {
      return
    }

    // 尝试模糊匹配
    for (const sourceCol of props.sourceColumns) {
      const sourceLower = sourceCol.toLowerCase()
      // 检查是否包含相同的关键词
      if (sourceLower.includes(targetLower) || targetLower.includes(sourceLower)) {
        mappings.push({
          source: sourceCol,
          target: targetCol,
          transform: ''
        })
        break
      }
    }
  })

  mappingList.value = mappings
}

// 源字段变化
function handleSourceChange(row) {
  // 如果源字段变化，自动填充转换规则中的字段名
  if (row.transform && row.transform.includes('${source}')) {
    row.transform = row.transform.replace('${source}', row.source)
  }
}

// 目标字段变化
function handleTargetChange(row) {
  // 如果没有设置源字段，尝试自动匹配
  if (!row.source && row.target) {
    const targetLower = row.target.toLowerCase()
    const matchedSource = props.sourceColumns.find(col =>
      col.toLowerCase() === targetLower
    )
    if (matchedSource) {
      row.source = matchedSource
    }
  }
}

// 插入转换规则
function handleInsertTransform(row, command) {
  row.transform = command
}

// 暴露方法
defineExpose({
  autoMap,
  clearMappings,
  addMapping: handleAddMapping
})
</script>

<style scoped lang="scss">
.field-mapping-editor {
  .mapping-actions {
    margin-top: 16px;
    padding: 12px;
    background: #f5f7fa;
    border-radius: 4px;
    display: flex;
    gap: 12px;
    align-items: center;

    .mapping-stats {
      margin-left: auto;
    }
  }

  .transform-btn {
    cursor: pointer;
    font-size: 12px;

    &:hover {
      color: #409EFF;
    }
  }
}

:deep(.el-table) {
  .el-select {
    width: 100%;
  }
}
</style>
