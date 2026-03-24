<template>
  <el-select
    :modelValue="modelValue"
    @update:modelValue="$emit('update:modelValue', $event)"
    @change="$emit('change', $event)"
    v-bind="$attrs"
  >
    <el-option
      v-for="ds in datasources"
      :key="ds.id"
      :label="ds.name"
      :value="ds.id"
    >
      <div class="datasource-option">
        <span class="ds-name">{{ ds.name }}</span>
        <el-tag size="small" :type="getTypeColor(ds.type)">{{ ds.type }}</el-tag>
      </div>
    </el-option>
  </el-select>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listDatasource as listDatasources } from '@/api/data/datasource'

defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  }
})

defineEmits(['update:modelValue', 'change'])

const datasources = ref([])

onMounted(async () => {
  try {
    const res = await listDatasources({ pageNum: 1, pageSize: 1000, status: '0' })
    datasources.value = res.rows || []
  } catch (error) {
    console.error('加载数据源列表失败:', error)
  }
})

function getTypeColor(type) {
  const colorMap = {
    mysql: 'primary',
    postgresql: 'success',
    hive: 'warning',
    oracle: 'danger'
  }
  return colorMap[type] || 'info'
}
</script>

<style scoped>
.datasource-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.ds-name {
  flex: 1;
}
</style>
