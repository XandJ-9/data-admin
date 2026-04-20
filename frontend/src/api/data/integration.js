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

export function updateTask(data) {
  const { taskId, ...payload } = data
  return request({
    url: '/dataintegration/task/' + taskId,
    method: 'put',
    data: payload
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

/**
 * 获取支持的执行器类型列表
 */
export function getSupportedExecutors() {
  return [
    { value: 'mock', label: 'Mock执行器', description: '用于开发联调或无真实执行环境时的闭环验证' },
    { value: 'datax', label: 'DataX执行器', description: '用于真实数据同步执行，依赖后端 DataX 环境配置' }
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
