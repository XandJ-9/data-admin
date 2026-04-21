import request from '@/utils/request'

export function listScripts(query) {
  return request({
    url: '/datadev/scripts',
    method: 'get',
    params: query,
  })
}

export function getScript(id) {
  return request({
    url: `/datadev/scripts/${id}`,
    method: 'get',
  })
}

export function addScript(data) {
  return request({
    url: '/datadev/scripts',
    method: 'post',
    data,
  })
}

export function updateScript(id, data) {
  return request({
    url: `/datadev/scripts/${id}`,
    method: 'put',
    data,
  })
}

export function delScript(id) {
  return request({
    url: `/datadev/scripts/${id}`,
    method: 'delete',
  })
}

export function publishScriptTask(scriptId) {
  return request({
    url: `/datadev/scripts/${scriptId}/publish-task`,
    method: 'post',
  })
}

export function listVersions(scriptId) {
  return request({
    url: `/datadev/scripts/${scriptId}/versions`,
    method: 'get',
  })
}

export function createVersion(scriptId, data) {
  return request({
    url: `/datadev/scripts/${scriptId}/versions/create`,
    method: 'post',
    data,
  })
}

export function publishVersion(scriptId, data) {
  return request({
    url: `/datadev/scripts/${scriptId}/versions/publish`,
    method: 'post',
    data,
  })
}

export function rollbackVersion(scriptId, versionId) {
  return request({
    url: `/datadev/scripts/${scriptId}/versions/${versionId}/rollback`,
    method: 'post',
  })
}

export function executeScript(scriptId, data) {
  return request({
    url: `/datadev/scripts/${scriptId}/execute`,
    method: 'post',
    data,
    timeout: 30 * 60 * 1000,
  })
}

export function listScriptExecutions(scriptId, query) {
  return request({
    url: `/datadev/scripts/${scriptId}/executions`,
    method: 'get',
    params: query,
  })
}

export function listExecutions(query) {
  return request({
    url: '/datadev/executions',
    method: 'get',
    params: query,
  })
}

export function listDirectories(query) {
  return request({
    url: '/datadev/directories',
    method: 'get',
    params: query,
  })
}

export function getDirectoryTree() {
  return request({
    url: '/datadev/directories/tree',
    method: 'get',
  })
}

export function addDirectory(data) {
  return request({
    url: '/datadev/directories',
    method: 'post',
    data,
  })
}

export function updateDirectory(id, data) {
  return request({
    url: `/datadev/directories/${id}`,
    method: 'put',
    data,
  })
}

export function delDirectory(id) {
  return request({
    url: `/datadev/directories/${id}`,
    method: 'delete',
  })
}

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
