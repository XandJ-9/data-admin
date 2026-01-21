import request from '@/utils/request'

// Data Task APIs
export function listTask(query) {
  return request({
    url: '/datataskmonitor/tasks/',
    method: 'get',
    params: query
  })
}

export function getTask(id) {
  return request({
    url: '/datataskmonitor/tasks/' + id + '/',
    method: 'get'
  })
}

export function addTask(data) {
  return request({
    url: '/datataskmonitor/tasks/',
    method: 'post',
    data: data
  })
}

export function updateTask(data) {
  return request({
    url: '/datataskmonitor/tasks/' + data.id + '/',
    method: 'put',
    data: data
  })
}

export function delTask(id) {
  return request({
    url: '/datataskmonitor/tasks/' + id + '/',
    method: 'delete'
  })
}

export function startTask(id) {
    return request({
        url: '/datataskmonitor/tasks/' + id + '/start/',
        method: 'post'
    })
}

export function stopTask(id) {
    return request({
        url: '/datataskmonitor/tasks/' + id + '/stop/',
        method: 'post'
    })
}

export function pauseTask(id) {
    return request({
        url: '/datataskmonitor/tasks/' + id + '/pause/',
        method: 'post'
    })
}

// Task Log APIs
export function listTaskLog(query) {
  return request({
    url: '/datataskmonitor/logs/',
    method: 'get',
    params: query
  })
}

// Alert Rule APIs
export function listAlertRule(query) {
  return request({
    url: '/datataskmonitor/rules/',
    method: 'get',
    params: query
  })
}

export function addAlertRule(data) {
  return request({
    url: '/datataskmonitor/rules/',
    method: 'post',
    data: data
  })
}

export function updateAlertRule(data) {
  return request({
    url: '/datataskmonitor/rules/' + data.id + '/',
    method: 'put',
    data: data
  })
}

export function delAlertRule(id) {
  return request({
    url: '/datataskmonitor/rules/' + id + '/',
    method: 'delete'
  })
}

// Alert Record APIs
export function listAlertRecord(query) {
  return request({
    url: '/datataskmonitor/alerts/',
    method: 'get',
    params: query
  })
}

export function handleAlert(id, data) {
  return request({
    url: '/datataskmonitor/alerts/' + id + '/handle/',
    method: 'post',
    data: data
  })
}
