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

export function updateTask(taskId, data) {
  return request({
    url: '/dataintegration/task/' + taskId,
    method: 'put',
    data: { ...data, taskId }
  })
}

export function delTask(taskId) {
  return request({
    url: '/dataintegration/task/' + taskId,
    method: 'delete'
  })
}

