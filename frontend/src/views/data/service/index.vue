<template>
  <div class="app-container">
    <el-card>
      <template #header>
        <span>数据服务</span>
      </template>
      <p>此模块提供独立的数据查询服务页面。</p>
      <el-button type="primary" @click="$router.push('/dataservice/query')">进入查询</el-button>
    </el-card>
  </div>
</template>

<script setup name="DataService">
</script>

<style scoped>
</style>