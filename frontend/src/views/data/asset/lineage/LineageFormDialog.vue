<template>
  <el-dialog :title="title" v-model="dialogVisible" width="600px" append-to-body>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="源表" prop="sourceTableId">
        <el-select
          v-model="form.sourceTableId"
          placeholder="请选择源表"
          filterable
          clearable
          style="width: 100%"
        >
          <el-option
            v-for="table in tableOptions"
            :key="table.id"
            :label="`${table.tableName} (${table.databaseName || '-'})`"
            :value="table.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="目标表" prop="targetTableId">
        <el-select
          v-model="form.targetTableId"
          placeholder="请选择目标表"
          filterable
          clearable
          style="width: 100%"
        >
          <el-option
            v-for="table in tableOptions"
            :key="table.id"
            :label="`${table.tableName} (${table.databaseName || '-'})`"
            :value="table.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="血缘类型" prop="lineageType">
        <el-radio-group v-model="form.lineageType">
          <el-radio label="upstream">上游</el-radio>
          <el-radio label="downstream">下游</el-radio>
        </el-radio-group>
        <div class="form-item-tip">上游：数据来源表，下游：数据目标表</div>
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          placeholder="请输入描述"
          :rows="3"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
const { proxy } = getCurrentInstance()

const props = defineProps({
  modelValue: Boolean,
  title: String,
  form: { type: Object, required: true },
  rules: Object,
  tableOptions: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'submit'])

const formRef = ref(null)

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

function handleCancel() {
  emit('update:modelValue', false)
}

function handleSubmit() {
  formRef.value.validate(valid => {
    if (!valid) return
    if (props.form.sourceTableId === props.form.targetTableId) {
      proxy.$modal.msgWarning('源表和目标表不能相同')
      return
    }
    emit('submit')
  })
}
</script>

<style scoped>
.form-item-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
