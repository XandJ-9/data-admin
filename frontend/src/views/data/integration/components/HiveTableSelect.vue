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

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  schema: {
    type: String,
    default: 'default'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const tables = ref([])
const loading = ref(false)

watch(
  () => props.schema,
  async (newSchema) => {
    if (newSchema) {
      await loadTables()
    }
  }
)

onMounted(async () => {
  await loadTables()
})

async function loadTables() {
  loading.value = true
  try {
    // TODO: 调用后端API获取Hive表列表
    // const res = await getHiveTables(props.schema)
    // tables.value = res.data || []

    // 模拟数据
    const schema = props.schema
    tables.value = [
      `${schema}.users`,
      `${schema}.orders`,
      `${schema}.products`
    ]
  } catch (error) {
    console.error('加载Hive表列表失败:', error)
  } finally {
    loading.value = false
  }
}
</script>
