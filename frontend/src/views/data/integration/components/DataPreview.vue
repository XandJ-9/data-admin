<template>
  <div class="data-preview">
    <el-table
      v-loading="loading"
      :data="previewData"
      stripe
      border
      max-height="400"
      style="width: 100%"
    >
      <el-table-column
        v-for="col in columns"
        :key="col"
        :prop="col"
        :label="col"
        min-width="120"
        show-overflow-tooltip
      />
    </el-table>
    <el-empty v-if="!loading && previewData.length === 0" description="暂无数据" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  sourceConfig: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const previewData = ref([])
const columns = ref([])

watch(
  () => props.sourceConfig,
  async (newConfig) => {
    if (newConfig?.datasourceId && newConfig?.table) {
      await loadPreviewData()
    }
  },
  { deep: true }
)

onMounted(async () => {
  if (props.sourceConfig?.datasourceId && props.sourceConfig?.table) {
    await loadPreviewData()
  }
})

async function loadPreviewData() {
  // TODO: 调用后端API获取预览数据
  // 预留接口，待后端实现
  // const res = await previewData(props.sourceConfig)
  // previewData.value = res.data
  // columns.value = res.columns
}
</script>

<style scoped>
.data-preview {
  padding: 8px 0;
}
</style>
