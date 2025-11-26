import request from '@/utils/request'

// 查询数据源列表
export function listDatasource(query) {
  return request({
    url: '/datasource/manage/list',
    method: 'get',
    params: query
  })
}

// 查询数据源详细
export function getDatasource(dataSourceId) {
  return request({
    url: '/datasource/manage/' + dataSourceId,
    method: 'get'
  })
}

// 新增数据源
export function addDatasource(data) {
  return request({
    url: '/datasource/manage',
    method: 'post',
    data: data
  })
}

// 修改数据源
export function updateDatasource(data) {
  return request({
    url: '/datasource/manage',
    method: 'put',
    data: data
  })
}

// 删除数据源（支持批量）
export function delDatasource(dataSourceId) {
  return request({
    url: '/datasource/manage/' + dataSourceId,
    method: 'delete'
  })
}

// 测试数据源连通性
export function testDatasource(dataSourceId) {
  return request({
    url: '/datasource/manage/' + dataSourceId + '/test',
    method: 'post'
  })
}

// 根据请求体测试数据源连通性（不落库）
export function testDatasourceByBody(data) {
  return request({
    url: '/datasource/manage/test',
    method: 'post',
    data: data
  })
}