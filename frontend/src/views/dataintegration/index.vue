<template>
  <div class="app-container">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>单表离线同步</span>
          </template>
          <div>
            <p>支持将单个数据库中的表数据同步到另一个数据库中的表。</p>
            <el-button type="primary" @click="createTask('single')">创建任务</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>分库分表离线同步</span>
          </template>
          <div>
            <p>支持将多个数据库中的表数据同步到另一个数据源的单个表中。</p>
            <el-button type="primary" @click="createTask('multi')">创建任务</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
  
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()

function createTask(type) {
  router.push({ name: 'DataIntegrationTaskDetail', params: { id: 'new' }, query: { type } })
}
</script>

<style scoped>
</style>

