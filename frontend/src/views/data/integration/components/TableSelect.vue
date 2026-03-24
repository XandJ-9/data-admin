<template>
  <el-select
    :modelValue="modelValue"
    @update:modelValue="$emit('update:modelValue', $event)"
    @change="$emit('change', $event)"
    :loading="loading"
    :filterable="true"
    v-bind="$attrs"
  >
    <el-option
      v-for="table in tables"
      :key="table"
      :label="table"
      :value="table"
    />
  </el-select>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { listDatasource as getTableList } from '@/api/data/datasource'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  datasourceId: {
    type: [String, Number],
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const tables = ref([])
const loading = ref(false)

watch(
  () => props.datasourceId,
  async (newId) => {
    if (newId) {
      await loadTables()
    } else {
      tables.value = []
    }
  }
)

onMounted(async () => {
  if (props.datasourceId) {
    await loadTables()
  }
})

async function loadTables() {
  loading.value = true
  try {
    // TODO: 调用后端API获取表列表
    // const res = await getTableList(props.datasourceId)
    // tables.value = res.data || []

    // 模拟数据
    tables.value = ['users', 'orders', 'products', 'categories']
  } catch (error) {
    console.error('加载表列表失败:', error)
  } finally {
    loading.value = false
  }
}
</script>
