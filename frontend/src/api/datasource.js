import request from '@/utils/request'

// 查询数据源列表
export function listDatasource(query) {
  return request({
    url: '/datasource/',
    method: 'get',
    params: query,
    headers: {
      'repeatSubmit': false
    }
  })
}

// 查询数据源详细
export function getDatasource(dataSourceId) {
  return request({
    url: '/datasource/' + dataSourceId,
    method: 'get'
  })
}

// 新增数据源
export function addDatasource(data) {
  return request({
    url: '/datasource/',
    method: 'post',
    data: data
  })
}

// 修改数据源
export function updateDatasource(data) {
  return request({
    url: '/datasource/' + data.dataSourceId,
    method: 'put',
    data: data
  })
}

// 删除数据源（REST，支持批量以逗号分隔ID）
export function delDatasource(dataSourceId) {
  return request({
    url: '/datasource/' + dataSourceId,
    method: 'delete'
  })
}

// 测试数据源连通性（REST，按资源ID）
export function testDatasource(dataSourceId) {
  return request({
    url: '/datasource/' + dataSourceId + '/test',
    method: 'post'
  })
}

// 根据请求体测试数据源连通性（REST，不落库）
export function testDatasourceByBody(data) {
  return request({
    url: '/datasource/test',
    method: 'post',
    data: data
  })
}


export function listDatabases(data) {
  return request({
    url: '/datasource/databases',
    method: 'post',
    data: data,
    headers: {
      'repeatSubmit': false
    }
  })
}

export function listTables(data) {
  return request({
    url: '/datasource/tables',
    method: 'post',
    data: data,
    headers: {
      'repeatSubmit': false
    }
  })
}

export function listColumns(data) {
  return request({
    url: '/datasource/columns',
    method: 'post',
    data: data,
    headers: {
      'repeatSubmit': false
    }
  })
}
export function collectMeta(data) {
  return request({
    url: '/datasource/collect',
    method: 'post',
    data: data
  })
}

export function collectMetaTable(data) {
  return request({
    url: '/datasource/collect-table',
    method: 'post',
    data: data
  })
}