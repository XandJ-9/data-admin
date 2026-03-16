import request from '@/utils/request'

// ==================== ETL任务管理 ====================

/**
 * 查询ETL任务列表
 * @param {Object} query 查询参数
 */
export function listETLTask(query) {
  return request({
    url: '/dataetl/tasks',
    method: 'get',
    params: query
  })
}

/**
 * 查询ETL任务详细信息
 * @param {Number} id 任务ID
 */
export function getETLTask(id) {
  return request({
    url: `/dataetl/tasks/${id}`,
    method: 'get'
  })
}

/**
 * 新增ETL任务
 * @param {Object} data 任务数据
 */
export function addETLTask(data) {
  return request({
    url: '/dataetl/tasks',
    method: 'post',
    data: data
  })
}

/**
 * 修改ETL任务
 * @param {Object} data 任务数据
 */
export function updateETLTask(data) {
  return request({
    url: '/dataetl/tasks',
    method: 'put',
    data: data
  })
}

/**
 * 删除ETL任务
 * @param {Number|Array} ids 任务ID
 */
export function delETLTask(ids) {
  return request({
    url: `/dataetl/tasks/${ids}`,
    method: 'delete'
  })
}

/**
 * 获取ETL任务简单列表（用于下拉框）
 */
export function listETLTaskSimple() {
  return request({
    url: '/dataetl/tasks/simple',
    method: 'get'
  })
}

/**
 * 执行ETL任务
 * @param {Number} id 任务ID
 */
export function executeETLTask(id) {
  return request({
    url: `/dataetl/tasks/${id}/execute`,
    method: 'post'
  })
}

/**
 * 验证DataX配置
 * @param {Number} id 任务ID
 */
export function validateETLConfig(id) {
  return request({
    url: `/dataetl/tasks/${id}/validate-config`,
    method: 'post'
  })
}

/**
 * 生成DataX配置
 * @param {Number} id 任务ID
 * @param {Object} params 参数
 */
export function generateDataXConfig(id, params) {
  return request({
    url: `/dataetl/tasks/${id}/datx-config`,
    method: 'get',
    params: params
  })
}

/**
 * 模拟执行（不实际写入数据）
 * @param {Number} id 任务ID
 */
export function dryRunETLTask(id) {
  return request({
    url: `/dataetl/tasks/${id}/execute-dry-run`,
    method: 'post'
  })
}

/**
 * 从模板创建任务
 * @param {Object} data 模板参数
 */
export function createTaskFromTemplate(data) {
  return request({
    url: '/dataetl/tasks/from-template',
    method: 'post',
    data: data
  })
}

/**
 * 克隆任务
 * @param {Number} id 任务ID
 * @param {Object} data 克隆参数
 */
export function cloneETLTask(id, data) {
  return request({
    url: `/dataetl/tasks/${id}/clone`,
    method: 'post',
    data: data
  })
}

/**
 * 获取任务统计信息
 * @param {Number} id 任务ID
 * @param {Number} days 天数
 */
export function getTaskStatistics(id, days = 7) {
  return request({
    url: `/dataetl/tasks/${id}/statistics`,
    method: 'get',
    params: { days }
  })
}

// ==================== 任务版本管理 ====================

/**
 * 创建任务版本快照
 * @param {Number} id 任务ID
 * @param {Object} data 版本数据
 */
export function createETLTaskVersion(id, data) {
  return request({
    url: `/dataetl/tasks/${id}/create-version`,
    method: 'post',
    data: data
  })
}

/**
 * 获取任务的所有版本
 * @param {Number} id 任务ID
 */
export function listETLTaskVersion(id) {
  return request({
    url: `/dataetl/tasks/${id}/versions`,
    method: 'get'
  })
}

/**
 * 回滚到指定版本
 * @param {Number} id 任务ID
 * @param {Object} data 版本数据
 */
export function rollbackETLTaskVersion(id, data) {
  return request({
    url: `/dataetl/tasks/${id}/rollback`,
    method: 'post',
    data: data
  })
}

// ==================== 字段映射管理 ====================

/**
 * 查询字段映射列表
 * @param {Object} query 查询参数
 */
export function listETLFieldMapping(query) {
  return request({
    url: '/dataetl/field-mappings',
    method: 'get',
    params: query
  })
}

/**
 * 查询字段映射详细信息
 * @param {Number} id 映射ID
 */
export function getETLFieldMapping(id) {
  return request({
    url: `/dataetl/field-mappings/${id}`,
    method: 'get'
  })
}

/**
 * 新增字段映射
 * @param {Object} data 映射数据
 */
export function addETLFieldMapping(data) {
  return request({
    url: '/dataetl/field-mappings',
    method: 'post',
    data: data
  })
}

/**
 * 修改字段映射
 * @param {Object} data 映射数据
 */
export function updateETLFieldMapping(data) {
  return request({
    url: '/dataetl/field-mappings',
    method: 'put',
    data: data
  })
}

/**
 * 删除字段映射
 * @param {Number|Array} ids 映射ID
 */
export function delETLFieldMapping(ids) {
  return request({
    url: `/dataetl/field-mappings/${ids}`,
    method: 'delete'
  })
}

/**
 * 批量创建字段映射
 * @param {Object} data 映射数据数组
 */
export function batchCreateFieldMapping(data) {
  return request({
    url: '/dataetl/field-mappings/batch',
    method: 'post',
    data: data
  })
}

// ==================== 执行日志管理 ====================

/**
 * 查询执行日志列表
 * @param {Object} query 查询参数
 */
export function listETLExecutionLog(query) {
  return request({
    url: '/dataetl/execution-logs',
    method: 'get',
    params: query
  })
}

/**
 * 查询执行日志详细信息
 * @param {Number} id 日志ID
 */
export function getETLExecutionLogDetail(id) {
  return request({
    url: `/dataetl/execution-logs/${id}/detail`,
    method: 'get'
  })
}

/**
 * 获取执行进度（实时）
 * @param {Number} id 日志ID
 */
export function getETLExecutionProgress(id) {
  return request({
    url: `/dataetl/execution-logs/${id}/progress`,
    method: 'get'
  })
}

/**
 * 取消执行
 * @param {Number} id 日志ID
 */
export function cancelETLExecution(id) {
  return request({
    url: `/dataetl/execution-logs/${id}/cancel`,
    method: 'post'
  })
}

// ==================== 水印管理 ====================

/**
 * 查询水印列表
 * @param {Object} query 查询参数
 */
export function listETLWatermark(query) {
  return request({
    url: '/dataetl/watermarks',
    method: 'get',
    params: query
  })
}

/**
 * 获取任务的最新水印值
 * @param {Number} taskId 任务ID
 */
export function getTaskWatermark(taskId) {
  return request({
    url: `/dataetl/watermarks/task/${taskId}`,
    method: 'get'
  })
}

// ==================== 任务模板管理 ====================

/**
 * 查询任务模板列表
 * @param {Object} query 查询参数
 */
export function listETLTaskTemplate(query) {
  return request({
    url: '/dataetl/templates',
    method: 'get',
    params: query
  })
}

/**
 * 查询任务模板详细信息
 * @param {Number} id 模板ID
 */
export function getETLTaskTemplate(id) {
  return request({
    url: `/dataetl/templates/${id}`,
    method: 'get'
  })
}

/**
 * 新增任务模板
 * @param {Object} data 模板数据
 */
export function addETLTaskTemplate(data) {
  return request({
    url: '/dataetl/templates',
    method: 'post',
    data: data
  })
}

/**
 * 修改任务模板
 * @param {Object} data 模板数据
 */
export function updateETLTaskTemplate(data) {
  return request({
    url: '/dataetl/templates',
    method: 'put',
    data: data
  })
}

/**
 * 删除任务模板
 * @param {Number|Array} ids 模板ID
 */
export function delETLTaskTemplate(ids) {
  return request({
    url: `/dataetl/templates/${ids}`,
    method: 'delete'
  })
}

/**
 * 获取系统模板列表
 */
export function listSystemTemplates() {
  return request({
    url: '/dataetl/templates/system',
    method: 'get'
  })
}

/**
 * 获取用户自定义模板列表
 */
export function listUserTemplates() {
  return request({
    url: '/dataetl/templates/user',
    method: 'get'
  })
}

/**
 * 从模板创建任务
 * @param {Object} data 模板参数
 */
export function createTaskFromTemplateAction(data) {
  return request({
    url: '/dataetl/templates/create-task',
    method: 'post',
    data: data
  })
}

/**
 * 增加模板使用次数
 * @param {Number} id 模板ID
 */
export function incrementTemplateUsage(id) {
  return request({
    url: `/dataetl/templates/${id}/increment-usage`,
    method: 'post'
  })
}

// ==================== 质检规则管理 ====================

/**
 * 查询质检规则列表
 * @param {Object} query 查询参数
 */
export function listETLQualityRule(query) {
  return request({
    url: '/dataetl/quality-rules',
    method: 'get',
    params: query
  })
}

/**
 * 查询质检规则详细信息
 * @param {Number} id 规则ID
 */
export function getETLQualityRule(id) {
  return request({
    url: `/dataetl/quality-rules/${id}`,
    method: 'get'
  })
}

/**
 * 新增质检规则
 * @param {Object} data 规则数据
 */
export function addETLQualityRule(data) {
  return request({
    url: '/dataetl/quality-rules',
    method: 'post',
    data: data
  })
}

/**
 * 修改质检规则
 * @param {Object} data 规则数据
 */
export function updateETLQualityRule(data) {
  return request({
    url: '/dataetl/quality-rules',
    method: 'put',
    data: data
  })
}

/**
 * 删除质检规则
 * @param {Number|Array} ids 规则ID
 */
export function delETLQualityRule(ids) {
  return request({
    url: `/dataetl/quality-rules/${ids}`,
    method: 'delete'
  })
}

/**
 * 测试质检规则
 * @param {Object} data 测试参数
 */
export function testETLQualityRule(data) {
  return request({
    url: '/dataetl/quality-rules/test',
    method: 'post',
    data: data
  })
}

/**
 * 切换规则启用状态
 * @param {Number} id 规则ID
 */
export function toggleQualityRuleEnabled(id) {
  return request({
    url: `/dataetl/quality-rules/${id}/toggle`,
    method: 'post'
  })
}

// ==================== 质检结果管理 ====================

/**
 * 查询质检结果列表
 * @param {Object} query 查询参数
 */
export function listETLQualityResult(query) {
  return request({
    url: '/dataetl/quality-results',
    method: 'get',
    params: query
  })
}

/**
 * 获取指定执行的所有质检结果
 * @param {String} executionId 执行ID
 */
export function getQualityResultsByExecution(executionId) {
  return request({
    url: `/dataetl/quality-results/execution/${executionId}`,
    method: 'get'
  })
}

// ==================== 执行进度管理 ====================

/**
 * 查询执行进度列表
 * @param {Object} query 查询参数
 */
export function listETLExecutionProgress(query) {
  return request({
    url: '/dataetl/execution-progress',
    method: 'get',
    params: query
  })
}

// ==================== 数据预览 ====================

/**
 * 预览源表数据
 * @param {Object} data 预览参数 {datasourceId, database, table, limit}
 */
export function previewSourceData(data) {
  return request({
    url: '/dataetl/preview/source',
    method: 'post',
    data: data,
    timeout: 60000
  })
}

/**
 * 预览SQL查询结果
 * @param {Object} data 查询参数 {datasourceId, sql, limit}
 */
export function previewQueryResult(data) {
  return request({
    url: '/dataetl/preview/query',
    method: 'post',
    data: data,
    timeout: 60000
  })
}

// ==================== 任务依赖 ====================

/**
 * 搜索可依赖的任务
 * @param {Object} query 搜索参数 {keyword, pageNum, pageSize}
 */
export function searchDependentTasks(query) {
  return request({
    url: '/dataetl/tasks/search',
    method: 'get',
    params: query
  })
}

/**
 * 获取任务的依赖列表
 * @param {Number} taskId 任务ID
 */
export function getTaskDependencies(taskId) {
  return request({
    url: `/dataetl/tasks/${taskId}/dependencies`,
    method: 'get'
  })
}

/**
 * 更新任务依赖
 * @param {Number} taskId 任务ID
 * @param {Object} data 依赖数据 {dependentTasks, dependencyStrategy, dependencyTimeout}
 */
export function updateTaskDependencies(taskId, data) {
  return request({
    url: `/dataetl/tasks/${taskId}/dependencies`,
    method: 'put',
    data: data
  })
}

// ==================== 表结构 ====================

/**
 * 获取数据源表结构
 * @param {Number} datasourceId 数据源ID
 * @param {String} database 数据库名
 * @param {String} table 表名
 */
export function getTableStructure(datasourceId, database, table) {
  return request({
    url: '/dataetl/table/structure',
    method: 'get',
    params: { datasourceId, database, table }
  })
}

/**
 * 自动创建表
 * @param {Object} data 建表参数
 */
export function autoCreateTable(data) {
  return request({
    url: '/dataetl/table/create',
    method: 'post',
    data: data
  })
}
