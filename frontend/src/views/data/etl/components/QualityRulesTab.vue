<template>
  <div>
    <div class="quality-actions">
      <el-button type="primary" icon="Plus" @click="$emit('add')">添加质检规则</el-button>
    </div>
    <el-table :data="rules" border stripe max-height="400">
      <el-table-column prop="ruleName" label="规则名称" min-width="150" />
      <el-table-column prop="ruleType" label="规则类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getTypeColor(row.ruleType)" size="small">
            {{ getTypeText(row.ruleType) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="ruleExpression" label="规则表达式" min-width="200" show-overflow-tooltip />
      <el-table-column prop="errorMessage" label="错误提示" min-width="150" show-overflow-tooltip />
      <el-table-column prop="enabled" label="启用状态" width="100" align="center">
        <template #default="{ row }">
          <el-switch v-model="row.enabled" @change="$emit('toggle', row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="center">
        <template #default="{ row }">
          <el-button link type="primary" icon="View" @click="$emit('view', row)">查看</el-button>
          <el-button link type="danger" icon="Delete" @click="$emit('delete', row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
defineProps({
  rules: { type: Array, default: () => [] }
})

defineEmits(['add', 'toggle', 'view', 'delete'])

function getTypeText(ruleType) {
  const texts = {
    completeness: '完整性', accuracy: '准确性', consistency: '一致性',
    timeliness: '及时性', validity: '有效性'
  }
  return texts[ruleType] || ruleType
}

function getTypeColor(ruleType) {
  const colors = {
    completeness: '', accuracy: 'success', consistency: 'warning',
    timeliness: 'danger', validity: 'info'
  }
  return colors[ruleType] || ''
}
</script>

<style scoped>
.quality-actions {
  margin-bottom: 16px;
}
</style>
