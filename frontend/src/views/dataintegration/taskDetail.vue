<template>
  <div class="app-container">
    <el-page-header :content="pageTitle" @back="goBack" />

    <div style="margin-top: 16px">
      <component :is="currentComp" ref="detailRef" />
    </div>

    <div style="margin-top: 16px; text-align: right">
      <el-button @click="goBack">返 回</el-button>
      <el-button type="primary" @click="handleSave">保 存</el-button>
    </div>
  </div>
</template>

<script setup>
import SingleTableSyncDetail from './offline/components/singleTableSyncDetail.vue'
import MultiTableSyncDetail from './offline/components/multiTableSyncDetail.vue'
import { useRoute, useRouter } from 'vue-router'
const route = useRoute()
const router = useRouter()
const { proxy } = getCurrentInstance()

const type = computed(() => (route.query.type || 'single'))
const pageTitle = computed(() => type.value === 'multi' ? '分库分表离线同步' : '单表离线同步')
const currentComp = computed(() => type.value === 'multi' ? MultiTableSyncDetail : SingleTableSyncDetail)
const detailRef = ref()

function goBack() {
  router.back()
}

function handleSave() {
  try {
    const data = detailRef.value?.getForm?.()
    if (!data) {
      proxy.$modal.msgError('表单未就绪')
      return
    }
    proxy.$modal.msgSuccess('已暂存任务配置')
    console.log('sync task payload', data)
  } catch (e) {
    proxy.$modal.msgError('保存失败')
  }
}
</script>

<style scoped>
</style>

