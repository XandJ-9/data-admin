<template>
  <div class="spark-config">
    <el-row>
      <el-col :span="12">
        <el-form-item label="应用名称" prop="config.appName">
          <el-input v-model="localConfig.appName" placeholder="请输入应用名称" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="主类" prop="config.mainClass">
          <el-input v-model="localConfig.mainClass" placeholder="请输入主类 (Main Class)" />
        </el-form-item>
      </el-col>
    </el-row>
    <el-form-item label="Jar包路径" prop="config.jar">
      <el-input v-model="localConfig.jar" placeholder="请输入Jar包路径" />
    </el-form-item>
    <el-form-item label="参数" prop="config.args">
      <el-input v-model="localConfig.args" type="textarea" placeholder="请输入参数" />
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ appName: '', mainClass: '', jar: '', args: '' })
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
