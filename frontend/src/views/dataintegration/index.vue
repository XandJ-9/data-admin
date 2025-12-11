<template>
  <div class="app-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>数据库同步到数据库</span>
          </template>
          <div>
            <el-button type="primary" @click="createTask('dbToDb')">创建任务</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>数据库同步到Hive</span>
          </template>
          <div>
            <el-button type="primary" @click="createTask('dbToHive')">创建任务</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>Hive同步到数据库</span>
          </template>
          <div>
            <el-button type="primary" @click="createTask('hiveToDb')">创建任务</el-button>
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

