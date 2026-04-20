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

/** 发布新版本 */
export function publishVersion(scriptId, data) {
  return request({
    url: `/datadev/scripts/${scriptId}/versions/publish`,
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
    timeout: 30 * 60 * 1000,
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

// ── 数据目录 ─────────────────────────────────

/** 查询数据目录列表 */
export function listDirectories(query) {
  return request({
    url: '/datadev/directories',
    method: 'get',
    params: query,
  })
}

/** 获取数据目录树 */
export function getDirectoryTree() {
  return request({
    url: '/datadev/directories/tree',
    method: 'get',
  })
}

/** 新增数据目录 */
export function addDirectory(data) {
  return request({
    url: '/datadev/directories',
    method: 'post',
    data,
  })
}

/** 修改数据目录 */
export function updateDirectory(id, data) {
  return request({
    url: `/datadev/directories/${id}`,
    method: 'put',
    data,
  })
}

/** 删除数据目录 */
export function delDirectory(id) {
  return request({
    url: `/datadev/directories/${id}`,
    method: 'delete',
  })
}


// ── 数据建模 ─────────────────────────────────

export function listModels(query) {
  return request({
    url: '/datadev/models',
    method: 'get',
    params: query,
  })
}

export function getModel(id) {
  return request({
    url: `/datadev/models/${id}`,
    method: 'get',
  })
}

export function addModel(data) {
  return request({
    url: '/datadev/models',
    method: 'post',
    data,
  })
}

export function updateModel(id, data) {
  return request({
    url: `/datadev/models/${id}`,
    method: 'put',
    data,
  })
}

export function delModel(id) {
  return request({
    url: `/datadev/models/${id}`,
    method: 'delete',
  })
}

export function submitModel(id) {
  return request({
    url: `/datadev/models/${id}/submit`,
    method: 'post',
  })
}
