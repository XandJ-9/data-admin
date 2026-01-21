import request from '@/utils/request'

export function listTasks(query) {
  return request({
    url: '/datastudio/tasks/',
    method: 'get',
    params: query
  })
}

export function getTask(taskId) {
  return request({
    url: '/datastudio/tasks/' + taskId + '/',
    method: 'get'
  })
}

export function addTask(data) {
  return request({
    url: '/datastudio/tasks/',
    method: 'post',
    data: data
  })
}

export function updateTask(taskId, data) {
  return request({
    url: '/datastudio/tasks/' + taskId + '/',
    method: 'put',
    data: data
  })
}

export function delTask(taskId) {
  return request({
    url: '/datastudio/tasks/' + taskId + '/',
    method: 'delete'
  })
}
