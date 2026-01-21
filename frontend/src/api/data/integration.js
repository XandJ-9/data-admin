import request from '@/utils/request'

export function listTasks(query) {
  return request({
    url: '/dataintegration/task',
    method: 'get',
    params: query
  })
}

export function getTask(taskId) {
  return request({
    url: '/dataintegration/task/' + taskId,
    method: 'get'
  })
}

export function addTask(data) {
  return request({
    url: '/dataintegration/task',
    method: 'post',
    data: data
  })
}

export function updateTask(taskId, data) {
  return request({
    url: '/dataintegration/task/' + taskId,
    method: 'put',
    data: { ...data, taskId }
  })
}

export function delTask(taskId) {
  return request({
    url: '/dataintegration/task/' + taskId,
    method: 'delete'
  })
}

// ==================== 任务执行 ====================

/**
 * 手动触发任务执行
 * @param {number} taskId - 任务ID
 */
export function executeTask(taskId) {
  return request({
    url: '/dataintegration/task/' + taskId + '/execute',
    method: 'post'
  })
}

/**
 * 查询任务执行历史
 * @param {number} taskId - 任务ID
 * @param {object} query - 查询参数 {pageNum, pageSize}
 */
export function getTaskExecutions(taskId, query) {
  return request({
    url: '/dataintegration/task/' + taskId + '/executions',
    method: 'get',
    params: query
  })
}

// ==================== 执行日志 ====================

/**
 * 查询执行日志列表
 * @param {object} query - 查询参数 {pageNum, pageSize, taskId, status}
 */
export function listExecutionLogs(query) {
  return request({
    url: '/dataintegration/executionlog',
    method: 'get',
    params: query
  })
}

/**
 * 获取执行日志详情
 * @param {number} logId - 日志ID
 */
export function getExecutionLogDetail(logId) {
  return request({
    url: '/dataintegration/executionlog/' + logId + '/detail',
    method: 'get'
  })
}

// ==================== 数据血缘 ====================

/**
 * 查询数据血缘
 * @param {object} query - 查询参数 {table, direction}
 * @param {string} query.table - 表名
 * @param {string} query.direction - 方向: upstream|downstream
 */
export function getLineage(query) {
  return request({
    url: '/dataintegration/lineage',
    method: 'get',
    params: query
  })
}

// ==================== 版本管理 ====================

/**
 * 查询任务版本列表
 * @param {object} query - 查询参数 {pageNum, pageSize, taskId}
 */
export function listTaskVersions(query) {
  return request({
    url: '/dataintegration/version',
    method: 'get',
    params: query
  })
}

/**
 * 激活指定版本
 * @param {number} versionId - 版本ID
 */
export function activateTaskVersion(versionId) {
  return request({
    url: '/dataintegration/version/' + versionId + '/activate',
    method: 'post'
  })
}

/**
 * 版本对比
 * @param {object} query - 查询参数 {version1, version2}
 */
export function compareTaskVersions(version1, version2) {
  return request({
    url: '/dataintegration/version/compare',
    method: 'get',
    params: { version1, version2 }
  })
}

/**
 * 获取支持的执行器类型列表
 */
export function getSupportedExecutors() {
  return [
    { value: 'datax', label: 'DataX执行器', description: '用于数据同步，支持多种数据源' },
    { value: 'spark_sql', label: 'Spark SQL执行器', description: '用于大数据处理和复杂转换' }
  ]
}

/**
 * 验证任务配置
 * @param {object} data - 任务配置数据
 */
export function validateTask(data) {
  return request({
    url: '/dataintegration/task/validate',
    method: 'post',
    data: data
  })
}
