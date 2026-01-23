<template>
  <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
    <el-form-item label="目标层级" prop="targetLayer" required>
      <el-radio-group v-model="formData.targetLayer">
        <el-radio label="dwd">DWD明细层</el-radio>
        <el-radio label="dws">DWS汇总层</el-radio>
        <el-radio label="ads">ADS应用层</el-radio>
      </el-radio-group>
      <div class="form-tip">选择计算结果要存储的目标层级</div>
    </el-form-item>

    <el-form-item label="SQL脚本" prop="sqlScript" required>
      <sql-editor
        v-model="formData.sqlScript"
        :height="300"
        placeholder="请输入Spark SQL语句，可以使用 {{ 参数名 }} 语法"
        language="sql"
      />
      <div class="form-tip">
        支持参数化查询，执行时会替换参数值
        <el-button link type="primary" size="small" @click="showSqlHelp">SQL帮助</el-button>
      </div>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive } from 'vue'
import SqlEditor from '../SqlEditor'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'show-sql-help'])

const formRef = ref()
const formData = reactive(props.modelValue)

const rules = {
  targetLayer: [{ required: true, message: '请选择目标层级', trigger: 'change' }],
  sqlScript: [{ required: true, message: '请输入SQL脚本', trigger: 'blur' }]
}

function showSqlHelp() {
  emit('show-sql-help')
}

async function validate() {
  return await formRef.value?.validate().catch(() => false)
}

defineExpose({
  validate
})
</script>

<style scoped>
.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
