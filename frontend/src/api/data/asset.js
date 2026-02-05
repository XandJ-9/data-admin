import request from '@/utils/request'

// ==================== 数据源管理 ====================

// 查询数据源列表
export function listDatasource(query) {
  return request({
    url: '/dataasset/datasource',
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
    url: '/dataasset/datasource/' + dataSourceId,
    method: 'get'
  })
}

// 新增数据源
export function addDatasource(data) {
  return request({
    url: '/dataasset/datasource',
    method: 'post',
    data: data
  })
}

// 修改数据源
export function updateDatasource(data) {
  return request({
    url: '/dataasset/datasource/' + data.dataSourceId,
    method: 'put',
    data: data
  })
}

// 删除数据源（REST，支持批量以逗号分隔ID）
export function delDatasource(dataSourceId) {
  return request({
    url: '/dataasset/datasource/' + dataSourceId,
    method: 'delete'
  })
}

// 测试数据源连通性（REST，按资源ID）
export function testDatasource(dataSourceId) {
  return request({
    url: '/dataasset/datasource/' + dataSourceId + '/test',
    method: 'post'
  })
}

// 根据请求体测试数据源连通性（REST，不落库）
export function testDatasourceByBody(data) {
  return request({
    url: '/dataasset/datasource/test',
    method: 'post',
    data: data
  })
}

// ==================== 元数据采集 ====================

// 获取数据库列表
export function listDatabases(data) {
  return request({
    url: '/dataasset/collection/databases',
    method: 'post',
    data: data,
    headers: {
      'repeatSubmit': false
    }
  })
}

// 获取数据源表列表
export function listTables(data) {
  return request({
    url: '/dataasset/collection/tables',
    method: 'post',
    data: data,
    headers: {
      'repeatSubmit': false
    },
    timeout: 60000
  })
}

// 获取表字段列表
export function listColumns(data) {
  return request({
    url: '/dataasset/collection/columns',
    method: 'post',
    data: data,
    headers: {
      'repeatSubmit': false
    }
  })
}

// 同步整库采集
export function collectMeta(data) {
  return request({
    url: '/dataasset/collection/collect',
    method: 'post',
    data: data
  })
}

// 单表采集
export function collectMetaTable(data) {
  return request({
    url: '/dataasset/collection/collect-table',
    method: 'post',
    data: data
  })
}

// 异步整库采集
export function collectMetaAsync(data) {
  return request({
    url: '/dataasset/collection/collect-async',
    method: 'post',
    data: data
  })
}

// 查询采集状态
export function getCollectStatus(taskId) {
  return request({
    url: '/dataasset/collection/collect-status',
    method: 'get',
    params: { taskId },
    headers: {
      'repeatSubmit': false
    }
  })
}

// 取消采集
export function cancelCollect(taskId) {
  return request({
    url: '/dataasset/collection/collect-cancel',
    method: 'post',
    data: { taskId }
  })
}

// ==================== 元数据表管理 ====================

// 查询元数据表列表
export function listMetaTables(query) {
  return request({
    url: '/dataasset/meta-table',
    method: 'get',
    params: query
  })
}

// 查询元数据表详细
export function getMetaTable(id) {
  return request({
    url: '/dataasset/meta-table/' + id,
    method: 'get'
  })
}

// 新增元数据表
export function addMetaTable(data) {
  return request({
    url: '/dataasset/meta-table',
    method: 'post',
    data: data
  })
}

// 修改元数据表
export function updateMetaTable(data) {
  return request({
    url: '/dataasset/meta-table/' + data.id,
    method: 'put',
    data: data
  })
}

// 删除元数据表（支持批量以逗号分隔 ID）
export function delMetaTable(idOrIds) {
  return request({
    url: '/dataasset/meta-table/' + idOrIds,
    method: 'delete'
  })
}

// ==================== 元数据字段管理 ====================

// 查询元数据字段列表
export function listMetaColumns(query) {
  return request({
    url: '/dataasset/meta-column',
    method: 'get',
    params: query
  })
}

// 查询元数据字段详细
export function getMetaColumn(id) {
  return request({
    url: '/dataasset/meta-column/' + id,
    method: 'get'
  })
}

// 新增元数据字段
export function addMetaColumn(data) {
  return request({
    url: '/dataasset/meta-column',
    method: 'post',
    data: data
  })
}

// 修改元数据字段
export function updateMetaColumn(data) {
  return request({
    url: '/dataasset/meta-column/' + data.id,
    method: 'put',
    data: data
  })
}

// 删除元数据字段（支持批量以逗号分隔 ID）
export function delMetaColumn(idOrIds) {
  return request({
    url: '/dataasset/meta-column/' + idOrIds,
    method: 'delete'
  })
}

// ==================== 表血缘管理 ====================

// 查询表血缘列表
export function listTableLineage(query) {
  return request({
    url: '/dataasset/lineage',
    method: 'get',
    params: query
  })
}

// 查询表血缘详细
export function getTableLineage(id) {
  return request({
    url: '/dataasset/lineage/' + id,
    method: 'get'
  })
}

// 新增表血缘
export function addTableLineage(data) {
  return request({
    url: '/dataasset/lineage',
    method: 'post',
    data: data
  })
}

// 修改表血缘
export function updateTableLineage(data) {
  return request({
    url: '/dataasset/lineage/' + data.id,
    method: 'put',
    data: data
  })
}

// 删除表血缘（支持批量以逗号分隔 ID）
export function delTableLineage(idOrIds) {
  return request({
    url: '/dataasset/lineage/' + idOrIds,
    method: 'delete'
  })
}

// 查询表的上游血缘
export function getUpstreamLineage(query) {
  return request({
    url: '/dataasset/lineage/upstream',
    method: 'get',
    params: query
  })
}

// 查询表的下游血缘
export function getDownstreamLineage(query) {
  return request({
    url: '/dataasset/lineage/downstream',
    method: 'get',
    params: query
  })
}

// 生成血缘关系图
export function getLineageGraph(query) {
  return request({
    url: '/dataasset/lineage/graph',
    method: 'get',
    params: query
  })
}
