import request from '@/utils/request'

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

// ==================== 规范数据资产查询 ====================

// 查询命名空间列表
export function listAssetNamespaces(query) {
  return request({
    url: '/dataasset/asset-namespace',
    method: 'get',
    params: query
  })
}

// 查询数据资产列表
export function listAssets(query) {
  return request({
    url: '/dataasset/asset',
    method: 'get',
    params: query
  })
}

// 查询数据资产详情
export function getAsset(id) {
  return request({
    url: '/dataasset/asset/' + id,
    method: 'get'
  })
}

// 查询数据资产字段列表
export function listAssetColumns(query) {
  return request({
    url: '/dataasset/asset-column',
    method: 'get',
    params: query
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
