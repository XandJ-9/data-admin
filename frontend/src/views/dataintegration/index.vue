<template>
  <div class="app-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>单表离线同步</span>
          </template>
          <div>
            <p>支持将单个数据库中的表数据同步到另一个数据库中的表。</p>
            <p>适用场景：将单数源下单张表的数据从同步到另一个指定的数据源下的指定表中</p>
            <el-button type="primary" @click="createTask('single')">创建任务</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>分库分表离线同步</span>
          </template>
          <div>
            <p>支持将多个数据库中的表数据同步到另一个数据源的单个表中。</p>
            <p>适用场景：将单个数据源下的多个分库分表同步到另一个指定数据源下的一张表中</p>
            <el-button type="primary" @click="createTask('multi')">创建任务</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>多数据源多租户数据库单表同步</span>
          </template>
          <div>
            <p>支持将多个数据源下的多个租户数据库中的所有表数据同步到另一个数据库中的指定表中。</p>
            <p>适用场景：将多个数据源下的多个租户数据库中的所有表数据同步到另一个数据库中的指定表中</p>
            <p>注意：多数据源下的每个租户数据库中的表数据同步到另一个数据库中的指定表中时，需要在任务配置中指定对应的租户数据库和表。</p>
            <el-button type="primary" @click="createTask('full')">创建任务</el-button>
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

