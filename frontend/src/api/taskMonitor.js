/**
 * 通用任务执行监控 API
 * 用于统一监控各类任务（ETL、元数据采集、质量检查等）的执行情况
 */
import request from '@/utils/request'

// 获取所有执行记录（通用）
export function listTaskExecutions(params) {
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

// 获取执行日志列表
export function listExecutionLogs(params) {
  return request({
    url: '/task-monitor/execution-logs/',
    method: 'get',
    params
  })
}
