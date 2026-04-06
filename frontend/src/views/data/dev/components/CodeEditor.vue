<template>
  <div class="code-editor">
    <!-- 工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <div class="doc-chip" :title="scriptName || '未命名脚本'">
          <span class="doc-chip-name">{{ scriptName || '未命名脚本' }}</span>
          <span class="doc-chip-lang">{{ aceLang.toUpperCase() }}</span>
        </div>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" size="small" :icon="CaretRight" :loading="running" @click="$emit('run')">
          运行当前文档
        </el-button>
        <el-button size="small" :icon="DocumentCopy" @click="$emit('save')" :disabled="!hasChange">
          保存草稿版本
        </el-button>
        <el-button type="success" size="small" :icon="UploadFilled" @click="$emit('publish')" :disabled="!hasChange">
          发布
        </el-button>
        <el-divider direction="vertical" />
        <el-button size="small" text :icon="FullScreen" @click="$emit('fullscreen')" title="全屏编辑" />
        <el-dropdown trigger="click" @command="onMenuCommand">
          <el-button size="small" text :icon="More" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="format">格式化</el-dropdown-item>
              <el-dropdown-item command="undo">撤销</el-dropdown-item>
              <el-dropdown-item command="redo">重做</el-dropdown-item>
              <el-dropdown-item divided command="settings">编辑器设置</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 编辑器主体 -->
    <div class="editor-body" ref="editorWrapperRef">
      <VAceEditor
        :value="modelValue"
        @update:value="onInput"
        :lang="aceLang"
        :theme="editorTheme"
        :options="aceOptions"
        style="width: 100%; height: 100%"
        @init="onEditorInit"
      />
    </div>
  </div>
</template>

<script setup>
import { VAceEditor } from 'vue3-ace-editor'
import 'ace-builds/src-noconflict/ext-language_tools'
import 'ace-builds/src-noconflict/mode-sql'
import 'ace-builds/src-noconflict/mode-python'
import 'ace-builds/src-noconflict/snippets/sql'
import 'ace-builds/src-noconflict/snippets/python'
import 'ace-builds/src-noconflict/theme-xcode'
import 'ace-builds/src-noconflict/theme-monokai'
import {
  CaretRight, DocumentCopy, FullScreen, More, UploadFilled,
} from '@element-plus/icons-vue'

defineOptions({ name: 'DevCodeEditor' })

const props = defineProps({
  modelValue: { type: String, default: '' },
  lang: { type: String, default: 'sql' },
  scriptName: { type: String, default: '' },
  running: { type: Boolean, default: false },
  hasChange: { type: Boolean, default: false },
  theme: { type: String, default: 'xcode' },
})

const emit = defineEmits(['update:modelValue', 'run', 'save', 'publish', 'fullscreen', 'cursor-change'])

const aceInstance = ref(null)
const editorWrapperRef = ref(null)

const aceLang = computed(() => (props.lang === 'python' ? 'python' : 'sql'))
const editorTheme = computed(() => props.theme)

const aceOptions = {
  fontSize: 14,
  showPrintMargin: false,
  wrap: true,
  tabSize: 4,
  enableBasicAutocompletion: true,
  enableLiveAutocompletion: true,
  enableSnippets: true,
  showLineNumbers: true,
  showGutter: true,
}

function onInput(val) {
  emit('update:modelValue', val)
}

function onEditorInit(editor) {
  aceInstance.value = editor
  // 光标位置变化上报
  editor.selection.on('changeCursor', () => {
    const pos = editor.getCursorPosition()
    emit('cursor-change', { row: pos.row + 1, col: pos.column + 1 })
  })
  // Ctrl/Cmd + Enter 执行
  editor.commands.addCommand({
    name: 'runScript',
    bindKey: { win: 'Ctrl-Enter', mac: 'Command-Enter' },
    exec: () => emit('run'),
  })
  // Ctrl/Cmd + S 保存
  editor.commands.addCommand({
    name: 'saveScript',
    bindKey: { win: 'Ctrl-S', mac: 'Command-S' },
    exec: () => emit('save'),
  })
}

function onMenuCommand(cmd) {
  const editor = aceInstance.value
  if (!editor) return
  switch (cmd) {
    case 'format':
      // 简易格式化：利用 ace beautify 扩展或保持原样
      try {
        const beautify = ace.require('ace/ext/beautify')
        if (beautify) beautify.beautify(editor.session)
      } catch { /* noop */ }
      break
    case 'undo':
      editor.undo()
      break
    case 'redo':
      editor.redo()
      break
    case 'settings':
      editor.execCommand('showSettingsMenu')
      break
  }
}

defineExpose({ getEditor: () => aceInstance.value })
</script>

<style lang="scss" scoped>
.code-editor {
  --editor-accent: #1f8f7a;

  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  border-bottom: 1px solid #dbe3ec;
  background: #fdfefe;
  flex-shrink: 0;
}

.toolbar-left {
  min-width: 0;
}

.doc-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  max-width: 320px;
  border: 1px solid #d6e5e0;
  background: #edf8f5;
  color: #21564a;
  border-radius: 999px;
  padding: 3px 12px;
}

.doc-chip-name {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
}

.doc-chip-lang {
  font-family: 'JetBrains Mono', 'SFMono-Regular', monospace;
  font-size: 11px;
  color: var(--editor-accent);
  background: #ddf2eb;
  padding: 1px 6px;
  border-radius: 999px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.editor-body {
  flex: 1;
  min-height: 0;
  position: relative;
}

@media (max-width: 768px) {
  .editor-toolbar {
    padding: 6px 8px;
    flex-wrap: wrap;
  }
  .toolbar-right {
    width: 100%;
    flex-wrap: wrap;
  }
  .doc-chip {
    max-width: 100%;
  }
  .doc-chip-name {
    max-width: 160px;
  }
}
</style>
