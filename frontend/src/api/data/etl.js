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

// ========== 依赖管理 API ==========

// 获取任务的所有依赖
export function getDependencies(taskId) {
  return request({
    url: `/dataetl/tasks/${taskId}/dependencies/`,
    method: 'get'
  })
}

// 添加任务依赖
export function addDependency(taskId, data) {
  return request({
    url: `/dataetl/tasks/${taskId}/add_dependency/`,
    method: 'post',
    data
  })
}

// 移除任务依赖
export function removeDependency(taskId, data) {
  return request({
    url: `/dataetl/tasks/${taskId}/remove_dependency/`,
    method: 'post',
    data
  })
}

// 检查任务是否可以执行
export function checkDependencies(taskId) {
  return request({
    url: `/dataetl/tasks/${taskId}/check_dependencies/`,
    method: 'get'
  })
}

// 获取完整依赖链
export function getDependencyChain(taskId) {
  return request({
    url: `/dataetl/tasks/${taskId}/dependency_chain/`,
    method: 'get'
  })
}

// ========== 通用执行监控 API ==========

// 获取所有执行记录（通用）
export function getAllTaskExecutions(params) {
  return request({
    url: '/task-monitor/executions/',
    method: 'get',
    params
  })
}

// 获取执行记录详情（通用）
export function getTaskExecution(id) {
  return request({
    url: `/task-monitor/executions/${id}/`,
    method: 'get'
  })
}

// 获取执行日志（通用）
export function getTaskExecutionLogs(id, params) {
  return request({
    url: `/task-monitor/executions/${id}/logs/`,
    method: 'get',
    params
  })
}

// 取消正在运行的任务
export function cancelExecution(id) {
  return request({
    url: `/task-monitor/executions/${id}/cancel/`,
    method: 'post'
  })
}

// 获取ETL特定执行详情
export function getETLExecutionDetails(id) {
  return request({
    url: `/task-monitor/executions/${id}/etl_details/`,
    method: 'get'
  })
}

// 获取执行日志列表
export function listExecutionLogs(params) {
  return request({
    url: '/task-monitor/execution-logs/',
    method: 'get',
    params
  })
}
