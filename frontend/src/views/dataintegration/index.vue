<template>
  <div class="app-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>单表离线同步</span>
          </template>
          <div>
            <p>支持将单个数据库中的表数据同步到另一个数据库中的表。</p>
            <p>适用场景：将单数源下单张表的数据从同步到另一个指定的数据源下的指定表中</p>
            <el-button type="primary" @click="createTask('dbTodb')">创建任务</el-button>
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

