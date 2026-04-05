import request from '@/utils/request'

// ── 脚本 CRUD ─────────────────────────────────

/** 查询脚本列表 */
export function listScripts(query) {
  return request({
    url: '/datadev/scripts',
    method: 'get',
    params: query,
  })
}

/** 获取脚本详情（含当前版本内容） */
export function getScript(id) {
  return request({
    url: `/datadev/scripts/${id}`,
    method: 'get',
  })
}

/** 创建脚本 */
export function addScript(data) {
  return request({
    url: '/datadev/scripts',
    method: 'post',
    data,
  })
}

/** 更新脚本 */
export function updateScript(id, data) {
  return request({
    url: `/datadev/scripts/${id}`,
    method: 'put',
    data,
  })
}

/** 删除脚本 */
export function delScript(id) {
  return request({
    url: `/datadev/scripts/${id}`,
    method: 'delete',
  })
}

// ── 版本管理 ─────────────────────────────────

/** 获取脚本版本列表 */
export function listVersions(scriptId) {
  return request({
    url: `/datadev/scripts/${scriptId}/versions`,
    method: 'get',
  })
}

/** 创建新版本 */
export function createVersion(scriptId, data) {
  return request({
    url: `/datadev/scripts/${scriptId}/versions/create`,
    method: 'post',
    data,
  })
}

/** 回滚到指定版本 */
export function rollbackVersion(scriptId, versionId) {
  return request({
    url: `/datadev/scripts/${scriptId}/versions/${versionId}/rollback`,
    method: 'post',
  })
}

// ── 执行 ─────────────────────────────────────

/** 触发脚本执行 */
export function executeScript(scriptId, data) {
  return request({
    url: `/datadev/scripts/${scriptId}/execute`,
    method: 'post',
    data,
  })
}

/** 获取脚本执行记录 */
export function listScriptExecutions(scriptId, query) {
  return request({
    url: `/datadev/scripts/${scriptId}/executions`,
    method: 'get',
    params: query,
  })
}

/** 获取全局执行记录 */
export function listExecutions(query) {
  return request({
    url: '/datadev/executions',
    method: 'get',
    params: query,
  })
}
