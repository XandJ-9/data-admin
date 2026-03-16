<template>
  <div class="sql-editor">
    <div class="editor-toolbar">
      <el-button size="small" @click="formatSQL">
        <el-icon><Document /></el-icon>
        格式化
      </el-button>
      <el-button size="small" @click="showHelp">
        <el-icon><QuestionFilled /></el-icon>
        帮助
      </el-button>
      <el-button size="small" @click="insertTemplate">
        <el-icon><MagicStick /></el-icon>
        模板
      </el-button>
    </div>
    <el-input
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      type="textarea"
      :placeholder="placeholder"
      :style="{ height: height + 'px' }"
      class="sql-textarea"
      spellcheck="false"
    />
  </div>
</template>

<script setup>
import { Document, QuestionFilled, MagicStick } from '@element-plus/icons-vue'

defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  height: {
    type: Number,
    default: 300
  },
  placeholder: {
    type: String,
    default: '请输入SQL语句...'
  },
  language: {
    type: String,
    default: 'sql'
  }
})

const emit = defineEmits(['update:modelValue'])

function formatSQL() {
  // TODO: 实现SQL格式化功能
  // 可以使用sql-formatter等库
}

function showHelp() {
  // 显示SQL帮助文档
}

function insertTemplate() {
  // 插入SQL模板
  const template = `-- Spark SQL模板
SELECT
    column1,
    column2,
    COUNT(*) AS cnt
FROM your_table
WHERE dt = '{{yyyyMMdd}}'
GROUP BY column1, column2
`
  emit('update:modelValue', template)
}
</script>

<style scoped>
.sql-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  gap: 8px;
  padding: 8px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
}

.sql-textarea {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.sql-textarea :deep(textarea) {
  font-family: inherit;
  border: none;
  resize: none;
}
</style>
