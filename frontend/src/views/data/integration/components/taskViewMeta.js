export const STATUS_OPTIONS = [
  { label: '草稿', value: 'draft' },
  { label: '启用', value: 'active' },
  { label: '暂停', value: 'paused' },
  { label: '归档', value: 'archived' },
]

export function buildDefaultTargetTableName(assetName, schemaName) {
  if (!assetName) {
    return ''
  }
  return (schemaName || '').trim().toLowerCase() === 'ods' ? `ods_${assetName}` : assetName
}

export function formatTargetTable(row) {
  if (!row?.targetSchemaName) {
    return row?.targetTableName || '-'
  }
  return `${row.targetSchemaName}.${row.targetTableName}`
}

export function loadTypeLabel(value) {
  return value === 'incremental' ? '增量' : '全量'
}

export function writeModeLabel(value) {
  const mapping = {
    overwrite: '覆盖',
    append: '追加',
    upsert: '更新插入',
  }
  return mapping[value] || value || '-'
}

export function executorLabel(value) {
  const mapping = {
    mock: 'Mock',
    datax: 'DataX',
  }
  return mapping[value] || value || '-'
}

export function statusLabel(value) {
  return STATUS_OPTIONS.find(item => item.value === value)?.label || value || '-'
}

export function statusTagType(value) {
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
    manual: '手动',
    cron: 'Cron',
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

export function executionStatusTagType(value) {
  const mapping = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    cancelled: 'info',
  }
  return mapping[value] || 'info'
}

export function formatJson(value) {
  try {
    return JSON.stringify(value || {}, null, 2)
  } catch (error) {
    return String(value || '{}')
  }
}
