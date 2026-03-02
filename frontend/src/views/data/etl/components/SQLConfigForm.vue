<template>
  <el-row :gutter="20">
    <el-col :span="24">
      <el-form-item label="SQL配置">
        <el-input
          v-model="formData.sqlConfig"
          type="textarea"
          :rows="6"
          placeholder="请输入SQL配置，支持Django Template语法，如：SELECT * FROM user_info WHERE update_time >= '{{last_sync_time}}'"
        />
        <div class="sql-config-tips">
          <el-text size="small" type="info">
            <el-icon><InfoFilled /></el-icon>
            支持变量：{{last_sync_time}}（上次同步时间）、{{execution_date}}（执行日期）
          </el-text>
        </div>
      </el-form-item>
    </el-col>
  </el-row>
</template>

<script setup>
import { computed } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const formData = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})
</script>

<style scoped>
.sql-config-tips {
  margin-top: 5px;
  line-height: 1.5;
}
</style>
