export function taskTypeLabel(value) {
  const mapping = {
    DATA_SYNC: '数据集成',
    SQL_COMPUTE: '加工作业',
    ASSET_COLLECTION: '资产采集',
  }
  return mapping[value] || value || '-'
}

export function taskTypeTag(value) {
  const mapping = {
    DATA_SYNC: 'success',
    SQL_COMPUTE: 'warning',
    ASSET_COLLECTION: 'primary',
  }
  return mapping[value] || 'info'
}

export function statusLabel(value) {
  const mapping = {
    draft: '草稿',
    active: '启用',
    paused: '暂停',
    archived: '归档',
  }
  return mapping[value] || value || '-'
}

export function statusTag(value) {
  const mapping = {
    draft: 'info',
    active: 'success',
    paused: 'warning',
    archived: 'danger',
  }
  return mapping[value] || 'info'
}

export function scheduleTypeLabel(value) {
  const mapping = {
    manual: '手动触发',
    cron: 'Cron 调度',
    dependency: '依赖触发',
  }
  return mapping[value] || value || '-'
}

export function executionStatusLabel(value) {
  const mapping = {
    pending: '等待执行',
    running: '执行中',
    success: '执行成功',
    failed: '执行失败',
    cancelled: '已取消',
  }
  return mapping[value] || value || '-'
}

export function executionStatusTag(value) {
  const mapping = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    cancelled: 'info',
  }
  return mapping[value] || 'info'
}

export function triggerModeLabel(value) {
  const mapping = {
    manual: '手动触发',
    schedule: '定时触发',
    dependency: '依赖触发',
  }
  return mapping[value] || value || '未知触发'
}

export function triggerModeTag(value) {
  const mapping = {
    manual: 'info',
    schedule: 'success',
    dependency: 'warning',
  }
  return mapping[value] || 'info'
}

export function sourceModuleLabel(value) {
  const mapping = {
    'dataintegration.task': '数据集成',
    'datadev.script': '建模与加工',
    'datasource.collection': '源数据采集',
  }
  return mapping[value] || value || '未归类'
}

export function sourceModuleTag(value) {
  const mapping = {
    'dataintegration.task': 'success',
    'datadev.script': 'warning',
    'datasource.collection': 'primary',
  }
  return mapping[value] || 'info'
}

export function formatLastRun(task) {
  if (!task?.lastInstanceAt) {
    return '暂无运行记录'
  }
  return `${executionStatusLabel(task.lastInstanceStatus)} · ${task.lastInstanceAt}`
}

export function formatJson(value) {
  try {
    return JSON.stringify(value || {}, null, 2)
  } catch (error) {
    return String(value || '{}')
  }
}

export function formatExecutionOutcome(instance = {}) {
  const summary = instance?.resultSummary || {}
  const scope = summary.collectionScope || instance?.runtimeConfig?.collectionScope || ''
  const totalTables = Number(summary.totalTables || 0)
  const successfulTables = Number(summary.successfulTables || 0)
  const failedTables = Number(summary.failedTables || 0)
  const skippedTables = Number(summary.skippedTables || 0)
  const currentTable = summary.currentTable || ''
  const errorMessage = instance?.errorMessage || ''

  if (scope === 'database') {
    if (instance?.status === 'running' && currentTable) {
      return `整库采集中：${successfulTables}/${totalTables}，当前 ${currentTable}`
    }
    if (instance?.status === 'failed' && errorMessage) {
      return `整库采集失败：成功 ${successfulTables}，失败 ${failedTables}，跳过 ${skippedTables}`
    }
    if (instance?.status === 'success') {
      return `整库采集完成：成功 ${successfulTables}/${totalTables}，跳过 ${skippedTables}`
    }
  }

  if (scope === 'table') {
    if (instance?.status === 'success') {
      return '单表采集成功'
    }
    if (instance?.status === 'failed' && errorMessage) {
      return '单表采集失败'
    }
  }

  if (instance?.status === 'failed') {
    return '执行失败'
  }
  if (instance?.status === 'success') {
    return '执行成功'
  }
  if (instance?.status === 'running') {
    return '执行中'
  }
  if (instance?.status === 'pending') {
    return '等待执行'
  }
  return '-'
}

export function formatDuration(value) {
  if (value === undefined || value === null || value === '') {
    return '--'
  }
  const seconds = Number(value)
  if (Number.isNaN(seconds)) {
    return '--'
  }
  if (seconds < 60) {
    return `${seconds}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainSeconds = Math.round((seconds % 60) * 100) / 100
  if (minutes < 60) {
    return `${minutes}m ${remainSeconds}s`
  }
  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60
  return `${hours}h ${remainMinutes}m`
}

export function formatExecutorType(value) {
  const mapping = {
    asset_collection: '资产采集执行器',
    sql_executor: 'SQL 执行器',
    python_executor: 'Python 执行器',
    datax: 'DataX 执行器',
    mvp: 'MVP 执行器',
    spark: 'Spark 执行器',
    hive: 'Hive 执行器',
    mysql: 'MySQL 执行器',
    postgresql: 'PostgreSQL 执行器',
    postgres: 'PostgreSQL 执行器',
    presto: 'Presto 执行器',
    trino: 'Trino 执行器',
    sqlite: 'SQLite 执行器',
    mock: 'Mock 执行器',
  }
  return mapping[value] || value || '未标记执行器'
}

export function formatTriggeredBy(value, triggerMode) {
  const normalizedValue = String(value || '').trim()
  if (!normalizedValue) {
    return triggerModeLabel(triggerMode)
  }
  if (normalizedValue === 'schedule') {
    return '系统调度'
  }
  if (normalizedValue === 'dependency') {
    return '依赖触发'
  }
  if (normalizedValue === 'manual') {
    return '手动触发'
  }
  return normalizedValue
}
