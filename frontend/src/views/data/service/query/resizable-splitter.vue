<template>
  <div
    class="resizable-splitter"
    :class="{ 'is-dragging': isDragging }"
    @mousedown="onMouseDown"
  >
    <div class="splitter-line"></div>
    <div class="splitter-handle">
      <el-icon :size="14"><DCaret /></el-icon>
    </div>
  </div>
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
const startPosition = ref(0)
const startSize = ref(0)
const containerSize = ref(0)
const minSize = ref(100) // 最小尺寸
const maxSize = ref(0) // 最大尺寸

function onMouseDown(e) {
  e.preventDefault()
  isDragging.value = true
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
    maxSize.value = containerSize.value - 8 - minSize.value // 8px 是分割条高度
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
  height: 8px;
  background-color: #f5f5f5;
  border-top: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
  z-index: 10;
}

.resizable-splitter:hover {
  background-color: #e8e8e8;
}

.resizable-splitter.is-dragging {
  background-color: #d0d0d0;
}

.splitter-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background-color: #d0d0d0;
  transform: translateY(-50%);
}

.splitter-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 20px;
  background-color: #fff;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.resizable-splitter:hover .splitter-handle {
  background-color: #f0f0f0;
}

.resizable-splitter.is-dragging .splitter-handle {
  background-color: #e0e0e0;
}
</style>
