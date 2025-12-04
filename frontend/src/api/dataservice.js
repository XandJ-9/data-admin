import request from '@/utils/request'

// 执行数据查询（请求体需包含 dataSourceId, sql, params, pageSize, offset）
export function executeQuery(data) {
  return request({
    url: '/dataservice/query',
    method: 'post',
    data: data
  })
}

// 导出数据查询结果（CSV，固定导出前10000行）
export function exportQuery(data) {
  return request({
    url: '/dataservice/export',
    method: 'post',
    data: data,
    responseType: 'blob'
  })
}

// 查询数据查询日志
export function listQueryLog(query) {
  return request({
    url: '/dataservice/query-log',
    method: 'get',
    params: query
  })
}

// 接口信息：列表
export function listInterfaceInfo(query) {
  return request({
    url: '/dataservice/interface-info',
    method: 'get',
    params: query
  })
}

// 接口信息：详情
export function getInterfaceInfo(interfaceId) {
  return request({
    url: '/dataservice/interface-info/' + interfaceId,
    method: 'get'
  })
}

// 接口信息：新增
export function addInterfaceInfo(data) {
  return request({
    url: '/dataservice/interface-info',
    method: 'post',
    data: data
  })
}

// 接口信息：修改（REST，按资源ID）
export function updateInterfaceInfo(data) {
  return request({
    url: '/dataservice/interface-info/' + data.interfaceId,
    method: 'put',
    data: data
  })
}

// 接口信息：删除（支持批量，逗号分隔ID）
export function delInterfaceInfo(interfaceId) {
  return request({
    url: '/dataservice/interface-info/' + interfaceId,
    method: 'delete'
  })
}

// 接口字段：列表（按接口ID过滤）
export function listInterfaceFields(query) {
  return request({
    url: '/dataservice/interface-field',
    method: 'get',
    params: query
  })
}

// 接口字段：详情
export function getInterfaceField(fieldId) {
  return request({
    url: '/dataservice/interface-field/' + fieldId,
    method: 'get'
  })
}

// 接口字段：新增
export function addInterfaceField(data) {
  return request({
    url: '/dataservice/interface-field',
    method: 'post',
    data: data
  })
}

// 接口字段：修改
export function updateInterfaceField(data) {
  return request({
    url: '/dataservice/interface-field/' + data.fieldId,
    method: 'put',
    data: data
  })
}

// 接口字段：删除（支持批量，逗号分隔ID）
export function delInterfaceField(fieldId) {
  return request({
    url: '/dataservice/interface-field/' + fieldId,
    method: 'delete'
  })
}

// 接口：测试连接（按ID）
export function testInterfaceById(interfaceId) {
  return request({
    url: '/dataservice/interface-info/' + interfaceId + '/test',
    method: 'post'
  })
}


// 接口：执行查询（按ID）
export function executeInterfaceById(interfaceId, data) {
  return request({
    url: '/dataservice/interface-info/' + interfaceId + '/execute',
    method: 'post',
    data: data
  })
}

// 接口：导出数据（按ID）
export function exportInterfaceById(interfaceId, data) {
  return request({
    url: '/dataservice/interface-info/' + interfaceId + '/export',
    method: 'post',
    data: data,
    responseType: 'blob'
  })
}

// 接口：导出数据（按请求体）
export function exportInterfaceByBody(data) {
  return request({
    url: '/dataservice/interface-info/export',
    method: 'post',
    data: data,
    responseType: 'blob'
  })
}