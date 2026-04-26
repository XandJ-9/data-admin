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
