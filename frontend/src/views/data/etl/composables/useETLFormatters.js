/**
 * ETL 模块辅助函数 - 类型文本、颜色映射、数值格式化
 */

export function getEtlTypeColor(etlType) {
  const colors = { extract: 'info', transform: 'success', load: 'warning', full: 'danger' }
  return colors[etlType] || ''
}

export function getEtlTypeText(etlType) {
  const texts = { extract: 'STG采集', transform: 'DWD转换', load: 'ODS加载', full: '全量ETL' }
  return texts[etlType] || etlType
}

export function getExecutorTypeText(executorType) {
  const texts = { mock: '模拟', datax: 'DataX', spark: 'Spark', python: 'Python' }
  return texts[executorType] || executorType
}

export function getExecutionStatusText(status) {
  const texts = {
    pending: '等待执行', running: '执行中',
    success: '成功', failed: '失败', cancelled: '已取消'
  }
  return texts[status] || status
}

export function getExecutionStatusColor(status) {
  const colors = {
    pending: 'info', running: 'warning',
    success: 'success', failed: 'danger', cancelled: ''
  }
  return colors[status] || ''
}

export function formatNumber(num) {
  if (!num) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

export function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function formatDuration(ms) {
  if (!ms) return '0ms'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const minutes = Math.floor(ms / 60000)
  const seconds = ((ms % 60000) / 1000).toFixed(0)
  return `${minutes}m${seconds}s`
}
