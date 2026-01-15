<template>
  <div class="shell-config">
      <CodeEditor v-model="localConfig.script" language="sh" height="300px" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import CodeEditor from '@/components/CodeEditor'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ script: '' })
  }
})

const emit = defineEmits(['update:modelValue'])

const localConfig = ref({ ...props.modelValue })

watch(() => props.modelValue, (val) => {
  if (JSON.stringify(val) !== JSON.stringify(localConfig.value)) {
    localConfig.value = { ...val }
  }
}, { deep: true })

watch(localConfig, (val) => {
  emit('update:modelValue', val)
}, { deep: true })
</script>
