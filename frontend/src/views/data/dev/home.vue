<template>
  <div class="datadev-home-page">
    <div class="hero-card">
      <div>
        <p class="hero-kicker">Data Development</p>
        <h2 class="hero-title">数据开发首页</h2>
        <p class="hero-desc">在统一 Task 中轴之上，按“脚本开发、数据目录、数据建模”三条主线进入不同能力模块。先选择操作，再进入具体工作区，减少首次进入时的信息负担。</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" @click="goToIde()">进入脚本开发</el-button>
        <el-button plain type="success" @click="goToModeling">进入数据建模</el-button>
      </div>
    </div>

    <div class="action-grid">
      <div class="action-card accent-blue">
        <h3>脚本开发</h3>
        <p>进入 SQL / Python 研发工作台，支持版本管理、执行反馈与统一任务接入。</p>
        <div class="card-actions">
          <el-button type="primary" @click="goToIde()">打开工作台</el-button>
          <el-button plain @click="goToIde('sql')">新建 SQL</el-button>
          <el-button plain @click="goToIde('python')">新建 Python</el-button>
        </div>
      </div>

      <div class="action-card accent-green">
        <h3>数据建模</h3>
        <p>维护数仓表结构、字段注释、分层归属与负责人，先做治理，再提交建表。</p>
        <div class="card-actions">
          <el-button type="success" plain @click="goToModeling">进入建模</el-button>
        </div>
      </div>

      <div class="action-card accent-orange">
        <h3>数据目录</h3>
        <p>管理脚本目录结构，梳理开发空间与脚本归属，减少未分配脚本的堆积。</p>
        <div class="card-actions">
          <el-button plain @click="goToCatalog">进入目录</el-button>
        </div>
      </div>
    </div>

    <div class="guide-grid">
      <div class="guide-card">
        <h3>推荐使用路径</h3>
        <ol>
          <li>先进入数据建模维护表注释、字段注释、负责人等治理信息。</li>
          <li>再进入脚本开发完成 SQL / Python 研发与版本迭代。</li>
          <li>脚本运行后在工作台底部查看结果与运维记录，统一回到 Task 体系追踪。</li>
        </ol>
      </div>
      <div class="guide-card">
        <h3>模块边界</h3>
        <ul>
          <li>脚本开发：承接 SQL_COMPUTE 研发与版本管理。</li>
          <li>数据建模：承接表结构治理与建表提交。</li>
          <li>数据目录：承接脚本组织与空间结构整理。</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'DataDevHome' })

const router = useRouter()

function goToIde(quickCreate = '') {
  const query = quickCreate ? { quickCreate } : undefined
  router.push({ path: '/datadev/ide', query })
}

function goToModeling() {
  router.push('/datadev/modeling')
}

function goToCatalog() {
  router.push('/datadev/catalog')
}
</script>

<style lang="scss" scoped>
.datadev-home-page {
  min-height: calc(100vh - 84px);
  padding: 18px;
  background: linear-gradient(140deg, #f7f3ea 0%, #eef6f5 55%, #f4f7fb 100%);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card,
.action-card,
.guide-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #d7dee8;
  border-radius: 16px;
  box-shadow: 0 12px 24px rgba(22, 39, 58, 0.06);
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 24px;
}

.hero-kicker {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #1f8f7a;
  text-transform: uppercase;
}

.hero-title {
  margin: 0;
  font-size: 30px;
  color: #213044;
}

.hero-desc {
  margin: 10px 0 0;
  max-width: 760px;
  line-height: 1.8;
  color: #66768b;
}

.hero-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex-shrink: 0;
}

.action-grid,
.guide-grid {
  display: grid;
  gap: 16px;
}

.action-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.guide-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.action-card,
.guide-card {
  padding: 20px;
}

.action-card h3,
.guide-card h3 {
  margin: 0;
  font-size: 18px;
  color: #213044;
}

.action-card p,
.guide-card li {
  font-size: 13px;
  line-height: 1.8;
  color: #66768b;
}

.action-card p {
  margin: 10px 0 0;
}

.card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.accent-blue { border-top: 4px solid #409eff; }
.accent-green { border-top: 4px solid #1f8f7a; }
.accent-orange { border-top: 4px solid #e6a23c; }

.guide-card ol,
.guide-card ul {
  margin: 12px 0 0;
  padding-left: 20px;
}

@media (max-width: 1024px) {
  .action-grid,
  .guide-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .datadev-home-page {
    min-height: calc(100vh - 72px);
    padding: 12px;
  }

  .hero-card {
    flex-direction: column;
  }

  .hero-actions {
    flex-wrap: wrap;
  }

  .hero-title {
    font-size: 24px;
  }
}
</style>
