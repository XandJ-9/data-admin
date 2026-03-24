<template>
  <el-form :model="form" label-width="150px" :disabled="!isEdit">
    <el-form-item label="执行参数配置">
      <el-input
        v-model="executorParamsJson"
        type="textarea"
        :rows="10"
        placeholder='执行参数配置（JSON格式），例如：{"concurrency": 1, "batchSize": 1000}'
      />
    </el-form-item>
  </el-form>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  form: { type: Object, required: true },
  isEdit: { type: Boolean, default: false }
})

const executorParamsJson = computed({
  get: () => {
    return props.form.executorParams ? JSON.stringify(props.form.executorParams, null, 2) : '{}'
  },
  set: (value) => {
    try {
      props.form.executorParams = JSON.parse(value)
    } catch { /* ignore parse error while typing */ }
  }
})
</script>
