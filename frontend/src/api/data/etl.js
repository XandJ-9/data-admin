/**
 * ETL模块API - 简化版
 */
import request from '@/utils/request'

// 获取ETL任务列表
export function listTasks(params) {
  return request({
    url: '/dataetl/tasks/',
    method: 'get',
    params
  })
}

// 获取ETL任务详情
export function getTask(id) {
  return request({
    url: `/dataetl/tasks/${id}/`,
    method: 'get'
  })
}

// 创建ETL任务
export function createTask(data) {
  return request({
    url: '/dataetl/tasks/',
    method: 'post',
    data
  })
}

// 更新ETL任务
export function updateTask(id, data) {
  return request({
    url: `/dataetl/tasks/${id}/`,
    method: 'put',
    data: Array.isArray(data) ? data[0] : data
  })
}

// 删除ETL任务
export function deleteTask(id) {
  return request({
    url: `/dataetl/tasks/${id}/`,
    method: 'delete'
  })
}

// 批量删除ETL任务
export function deleteTasks(ids) {
  return request({
    url: `/dataetl/tasks/`,
    method: 'delete',
    data: { ids }
  })
}

// 获取场景列表
export function getScenarios() {
  return request({
    url: '/dataetl/tasks/scenarios/',
    method: 'get'
  })
}

// 手动执行任务
export function executeTask(id) {
  return request({
    url: `/dataetl/tasks/${id}/execute/`,
    method: 'post'
  })
}

// 停止任务
export function stopTask(id) {
  return request({
    url: `/dataetl/tasks/${id}/stop/`,
    method: 'post'
  })
}

// 获取任务执行历史
export function getTaskExecutions(id, params) {
  return request({
    url: `/dataetl/tasks/${id}/executions/`,
    method: 'get',
    params
  })
}

// 获取执行记录列表
export function listExecutions(params) {
  return request({
    url: '/dataetl/executions/',
    method: 'get',
    params
  })
}

// 获取执行记录详情
export function getExecution(id) {
  return request({
    url: `/dataetl/executions/${id}/`,
    method: 'get'
  })
}

// 获取执行日志
export function getExecutionLogs(id) {
  return request({
    url: `/dataetl/executions/${id}/logs/`,
    method: 'get'
  })
}

// 获取执行进度
export function getExecutionProgress(id) {
  return request({
    url: `/dataetl/executions/${id}/progress/`,
    method: 'get'
  })
}

// 获取任务模板
export function getTemplates(params) {
  return request({
    url: '/dataetl/tasks/templates/',
    method: 'get',
    params
  })
}

// 应用模板
export function applyTemplate(id) {
  return request({
    url: `/dataetl/templates/${id}/apply/`,
    method: 'post'
  })
}
