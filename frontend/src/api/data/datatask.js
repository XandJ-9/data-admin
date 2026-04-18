import request from '@/utils/request'

export function listTasks(query) {
  return request({
    url: '/datatask/task',
    method: 'get',
    params: query
  })
}

export function getTask(taskId) {
  return request({
    url: '/datatask/task/' + taskId,
    method: 'get'
  })
}

export function updateTask(taskId, data) {
  return request({
    url: '/datatask/task/' + taskId,
    method: 'put',
    data
  })
}

export function executeTask(taskId) {
  return request({
    url: '/datatask/task/' + taskId + '/execute',
    method: 'post'
  })
}

export function listTaskInstances(query) {
  return request({
    url: '/datatask/task-instance',
    method: 'get',
    params: query
  })
}

export function getTaskInstances(taskId, query) {
  return request({
    url: '/datatask/task/' + taskId + '/instances',
    method: 'get',
    params: query
  })
}

export function listTaskDependencies(query) {
  return request({
    url: '/datatask/task-dependency',
    method: 'get',
    params: query
  })
}

export function addTaskDependency(data) {
  return request({
    url: '/datatask/task-dependency',
    method: 'post',
    data
  })
}

export function updateTaskDependency(data) {
  const { dependencyId, ...payload } = data
  return request({
    url: '/datatask/task-dependency/' + dependencyId,
    method: 'put',
    data: payload
  })
}

export function delTaskDependency(dependencyId) {
  return request({
    url: '/datatask/task-dependency/' + dependencyId,
    method: 'delete'
  })
}
