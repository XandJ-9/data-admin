<template>
  <div class="dev-home-page">
    <section class="hero-card">
      <div>
        <p class="hero-kicker">Model Driven Data Development</p>
        <h2 class="hero-title">建模与加工</h2>
        <p class="hero-desc">
          ODS 进入仓库后，先定义目标模型，再围绕模型编写加工作业；真正的调度、依赖和运行治理统一进入任务运维。
        </p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" @click="goToJobs()">进入加工作业</el-button>
        <el-button type="success" plain @click="goToModeling">进入模型设计</el-button>
      </div>
    </section>

    <section class="card-grid">
      <article class="action-card accent-green">
        <h3>模型设计</h3>
        <p>先定义层级、目标表、字段注释和负责人，把治理信息前置到开发入口。</p>
        <div class="card-actions">
          <el-button type="success" plain @click="goToModeling">打开模型设计</el-button>
        </div>
      </article>

      <article class="action-card accent-blue">
        <h3>加工作业</h3>
        <p>围绕模型编写 SQL / Python 作业，保存草稿、发布版本、调试执行，再发布到任务运维。</p>
        <div class="card-actions">
          <el-button type="primary" @click="goToJobs()">查看作业</el-button>
          <el-button plain @click="goToJobs('sql')">新建 SQL 作业</el-button>
          <el-button plain @click="goToJobs('python')">新建 Python 作业</el-button>
        </div>
      </article>

      <article class="action-card accent-orange">
        <h3>任务运维</h3>
        <p>发布后的作业会进入统一 Task 中轴，在这里做 Cron、依赖、实例运行和异常处理。</p>
        <div class="card-actions">
          <el-button plain @click="goToTaskOps">进入任务运维</el-button>
        </div>
      </article>
    </section>

    <section class="guide-grid">
      <article class="guide-card">
        <h3>推荐使用路径</h3>
        <ol>
          <li>先在模型设计中维护层级、表注释、字段注释和负责人。</li>
          <li>再进入加工作业，绑定目标模型并编写 SQL / Python 逻辑。</li>
          <li>作业确认后点击“发布到任务运维”，在任务运维继续编排和调度。</li>
        </ol>
      </article>

      <article class="guide-card">
        <h3>模块边界</h3>
        <ul>
          <li>建模与加工只负责定义，不承接 Cron 与 DAG 编排。</li>
          <li>任务运维只负责运行，不直接改开发态 SQL。</li>
          <li>资产化会基于模型、任务和血缘锚点继续沉淀。</li>
        </ul>
      </article>
    </section>
  </div>
</template>

<script setup>
defineOptions({ name: 'DataDevHome' })

const router = useRouter()

function goToJobs(quickCreate = '') {
  const query = quickCreate ? { quickCreate } : undefined
  router.push({ path: '/datadev/ide', query })
}

function goToModeling() {
  router.push('/datadev/modeling')
}

function goToTaskOps() {
  router.push('/datatask')
}
</script>

<style lang="scss" scoped>
.dev-home-page {
  min-height: calc(100vh - 84px);
  padding: 18px;
  background: linear-gradient(140deg, #f5f8fc 0%, #eef7f4 58%, #fbf8ef 100%);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card,
.action-card,
.guide-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #dce5ef;
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

.hero-actions,
.card-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.hero-actions {
  align-items: flex-start;
  flex-shrink: 0;
}

.card-grid,
.guide-grid {
  display: grid;
  gap: 16px;
}

.card-grid {
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
  .card-grid,
  .guide-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dev-home-page {
    min-height: calc(100vh - 72px);
    padding: 12px;
  }

  .hero-card {
    flex-direction: column;
  }

  .hero-title {
    font-size: 24px;
  }
}
</style>
