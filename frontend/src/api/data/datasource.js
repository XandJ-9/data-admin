import request from '@/utils/request'

// 查询数据源列表
export function listDatasource(query) {
  return request({
    url: '/datasource/datasource',
    method: 'get',
    params: query
  })
}

// 查询数据源详细
export function getDatasource(dataSourceId) {
  return request({
    url: '/datasource/datasource/' + dataSourceId,
    method: 'get'
  })
}

// 新增数据源
export function addDatasource(data) {
  return request({
    url: '/datasource/datasource',
    method: 'post',
    data: data
  })
}

// 修改数据源
export function updateDatasource(data) {
  return request({
    url: '/datasource/datasource/' + data.dataSourceId,
    method: 'put',
    data: data
  })
}

// 删除数据源（REST，支持批量以逗号分隔ID）
export function delDatasource(dataSourceId) {
  return request({
    url: '/datasource/datasource/' + dataSourceId,
    method: 'delete'
  })
}

// 测试数据源连通性（REST，按资源ID）
export function testDatasource(dataSourceId) {
  return request({
    url: '/datasource/datasource/' + dataSourceId + '/test',
    method: 'post'
  })
}

// 根据请求体测试数据源连通性（REST，不落库）
export function testDatasourceByBody(data) {
  return request({
    url: '/datasource/datasource/test',
    method: 'post',
    data: data
  })
}

// 获取数据库列表
export function listDatabases(data) {
  return request({
    url: '/datasource/collection/databases',
    method: 'post',
    data: data,
    headers: {
      repeatSubmit: false
    }
  })
}

// 获取数据源表列表
export function listTables(data) {
  return request({
    url: '/datasource/collection/tables',
    method: 'post',
    data: data,
    headers: {
      repeatSubmit: false
    },
    timeout: 60000
  })
}

// 获取表字段列表
export function listColumns(data) {
  return request({
    url: '/datasource/collection/columns',
    method: 'post',
    data: data,
    headers: {
      repeatSubmit: false
    }
  })
}

// 同步整库采集
export function collectMeta(data) {
  return request({
    url: '/datasource/collection/collect',
    method: 'post',
    data: data
  })
}

// 单表采集
export function collectMetaTable(data) {
  return request({
    url: '/datasource/collection/collect-table',
    method: 'post',
    data: data
  })
}

// 异步整库采集
export function collectMetaAsync(data) {
  return request({
    url: '/datasource/collection/collect-async',
    method: 'post',
    data: data
  })
}

// 查询采集状态
export function getCollectStatus(taskId) {
  return request({
    url: '/datasource/collection/collect-status',
    method: 'get',
    params: { taskId },
    headers: {
      repeatSubmit: false
    }
  })
}

// 取消采集
export function cancelCollect(taskId) {
  return request({
    url: '/datasource/collection/collect-cancel',
    method: 'post',
    data: { taskId }
  })
}
