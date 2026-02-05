<template>
  <el-tooltip content="拖拽调整编辑器和结果区的高度" placement="right" :show-after="500">
    <div
      class="resizable-splitter"
      :class="{ 'is-dragging': isDragging }"
      @mousedown="onMouseDown"
    >
      <div class="splitter-line"></div>
      <div class="splitter-handle">
        <el-icon :size="16" class="handle-icon"><DCaret /></el-icon>
      </div>
      <div class="splitter-hint" v-if="!hasInteracted">
        <span>拖拽调整</span>
      </div>
    </div>
  </el-tooltip>
</template>

<script setup>
import { DCaret } from '@element-plus/icons-vue'

const props = defineProps({
  direction: {
    type: String,
    default: 'horizontal' // 'horizontal' or 'vertical'
  }
})

const emit = defineEmits(['resize'])

const isDragging = ref(false)
const hasInteracted = ref(false) // 是否已经交互过（用于隐藏提示）
const startPosition = ref(0)
const startSize = ref(0)
const containerSize = ref(0)
const minSize = ref(150) // 最小尺寸
const maxSize = ref(0) // 最大尺寸

function onMouseDown(e) {
  e.preventDefault()
  isDragging.value = true
  hasInteracted.value = true // 用户开始拖拽，隐藏提示
  startPosition.value = props.direction === 'horizontal' ? e.clientY : e.clientX

  // 获取父容器（tab-content）
  const container = e.target.closest('.tab-content')
  const prevElement = e.target.parentElement?.previousElementSibling
  const nextElement = e.target.parentElement?.nextElementSibling

  if (container) {
    containerSize.value = props.direction === 'horizontal'
      ? container.offsetHeight
      : container.offsetWidth
  }

  if (prevElement) {
    startSize.value = props.direction === 'horizontal'
      ? prevElement.offsetHeight
      : prevElement.offsetWidth
  }

  // 计算最大尺寸（总高度 - 分割条高度 - 下一元素最小高度）
  if (nextElement && container) {
    maxSize.value = containerSize.value - 12 - 100 // 12px 是分割条高度
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)

  // 防止拖拽时选中文本
  document.body.style.userSelect = 'none'
}

function onMouseMove(e) {
  if (!isDragging.value) return

  const currentPosition = props.direction === 'horizontal' ? e.clientY : e.clientX
  const delta = currentPosition - startPosition.value
  let newSize = startSize.value + delta

  // 限制在最小和最大尺寸之间
  newSize = Math.max(minSize.value, Math.min(maxSize.value, newSize))

  emit('resize', newSize)
}

function onMouseUp() {
  isDragging.value = false
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  document.body.style.userSelect = ''
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
})
</script>

<style scoped>
.resizable-splitter {
  position: relative;
  height: 12px;
  background: linear-gradient(to bottom, #f5f5f5 0%, #e8e8e8 50%, #f5f5f5 100%);
  border-top: 2px solid #d0d0d0;
  border-bottom: 2px solid #d0d0d0;
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  z-index: 10;
}

.resizable-splitter:hover {
  background: linear-gradient(to bottom, #e8e8e8 0%, #d8d8d8 50%, #e8e8e8 100%);
  border-top-color: #409eff;
  border-bottom-color: #409eff;
  height: 14px;
}

.resizable-splitter.is-dragging {
  background: linear-gradient(to bottom, #d8d8d8 0%, #c8c8c8 50%, #d8d8d8 100%);
  border-top-color: #409eff;
  border-bottom-color: #409eff;
  height: 14px;
}

.splitter-line {
  position: absolute;
  top: 50%;
  left: 20px;
  right: 20px;
  height: 2px;
  background: linear-gradient(to right, transparent, #d0d0d0 20%, #d0d0d0 80%, transparent);
  transform: translateY(-50%);
  opacity: 0.6;
}

.resizable-splitter:hover .splitter-line {
  opacity: 1;
  background: linear-gradient(to right, transparent, #409eff 20%, #409eff 80%, transparent);
}

.splitter-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 24px;
  background-color: #fff;
  border: 2px solid #d0d0d0;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.resizable-splitter:hover .splitter-handle {
  background-color: #409eff;
  border-color: #409eff;
  transform: scale(1.05);
  box-shadow: 0 3px 8px rgba(64, 158, 255, 0.3);
}

.resizable-splitter:hover .handle-icon {
  color: #fff;
}

.resizable-splitter.is-dragging .splitter-handle {
  background-color: #409eff;
  border-color: #409eff;
  transform: scale(1.1);
}

.resizable-splitter.is-dragging .handle-icon {
  color: #fff;
}

.handle-icon {
  color: #909399;
  transition: color 0.3s ease;
}

.splitter-hint {
  position: absolute;
  right: 70px;
  top: 50%;
  transform: translateY(-50%);
  background-color: rgba(64, 158, 255, 0.9);
  color: white;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  animation: fadeIn 0.5s ease;
  pointer-events: none;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-50%) translateX(10px);
  }
  to {
    opacity: 1;
    transform: translateY(-50%) translateX(0);
  }
}
</style>
