import request from '@/utils/request'

// ==================== ETL 任务管理 ====================

// ETL任务：列表查询
export function listETLTask(query) {
  return request({
    url: '/dataetl/tasks',
    method: 'get',
    params: query
  })
}

// ETL任务：简单列表（用于下拉框）
export function listETLTaskSimple() {
  return request({
    url: '/dataetl/tasks/simple',
    method: 'get'
  })
}

// ETL任务：详情
export function getETLTask(taskId) {
  return request({
    url: '/dataetl/tasks/' + taskId,
    method: 'get'
  })
}

// ETL任务：新增
export function addETLTask(data) {
  return request({
    url: '/dataetl/tasks',
    method: 'post',
    data: data
  })
}

// ETL任务：修改
export function updateETLTask(data) {
  return request({
    url: '/dataetl/tasks/' + data.taskId,
    method: 'put',
    data: data
  })
}

// ETL任务：删除（支持批量，逗号分隔ID）
export function delETLTask(taskId) {
  return request({
    url: '/dataetl/tasks/' + taskId,
    method: 'delete'
  })
}

// ETL任务：执行任务
export function executeETLTask(taskId) {
  return request({
    url: '/dataetl/tasks/' + taskId + '/execute',
    method: 'post'
  })
}

// ETL任务：创建版本快照
export function createETLTaskVersion(taskId, data) {
  return request({
    url: '/dataetl/tasks/' + taskId + '/create-version',
    method: 'post',
    data: data
  })
}

// ETL任务：获取版本列表
export function listETLTaskVersion(taskId) {
  return request({
    url: '/dataetl/tasks/' + taskId + '/versions',
    method: 'get'
  })
}

// ETL任务：回滚到指定版本
export function rollbackETLTaskVersion(taskId, data) {
  return request({
    url: '/dataetl/tasks/' + taskId + '/rollback',
    method: 'post',
    data: data
  })
}

// ==================== ETL 字段映射管理 ====================

// 字段映射：列表查询
export function listETLFieldMapping(query) {
  return request({
    url: '/dataetl/field-mappings',
    method: 'get',
    params: query
  })
}

// 字段映射：详情
export function getETLFieldMapping(mappingId) {
  return request({
    url: '/dataetl/field-mappings/' + mappingId,
    method: 'get'
  })
}

// 字段映射：新增
export function addETLFieldMapping(data) {
  return request({
    url: '/dataetl/field-mappings',
    method: 'post',
    data: data
  })
}

// 字段映射：批量新增
export function batchAddETLFieldMapping(data) {
  return request({
    url: '/dataetl/field-mappings/batch',
    method: 'post',
    data: data
  })
}

// 字段映射：修改
export function updateETLFieldMapping(data) {
  return request({
    url: '/dataetl/field-mappings/' + data.mappingId,
    method: 'put',
    data: data
  })
}

// 字段映射：删除（支持批量，逗号分隔ID）
export function delETLFieldMapping(mappingId) {
  return request({
    url: '/dataetl/field-mappings/' + mappingId,
    method: 'delete'
  })
}

// ==================== ETL 执行日志管理 ====================

// 执行日志：列表查询
export function listETLExecutionLog(query) {
  return request({
    url: '/dataetl/execution-logs',
    method: 'get',
    params: query
  })
}

// 执行日志：详情
export function getETLExecutionLog(logId) {
  return request({
    url: '/dataetl/execution-logs/' + logId,
    method: 'get'
  })
}

// 执行日志：详细信息
export function getETLExecutionLogDetail(logId) {
  return request({
    url: '/dataetl/execution-logs/' + logId + '/detail',
    method: 'get'
  })
}
