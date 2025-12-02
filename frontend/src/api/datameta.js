import request from '@/utils/request'

export function listMetaTables(query) {
  return request({
    url: '/datameta/meta-table',
    method: 'get',
    params: query
  })
}

export function listMetaColumns(query) {
  return request({
    url: '/datameta/meta-column',
    method: 'get',
    params: query
  })
}

// 新增元数据表
export function addMetaTable(data) {
  return request({
    url: '/datameta/meta-table',
    method: 'post',
    data: data
  })
}

// 修改元数据表
export function updateMetaTable(data) {
  return request({
    url: '/datameta/meta-table/' + data.id,
    method: 'put',
    data: data
  })
}

// 删除元数据表（支持批量以逗号分隔 ID）
export function delMetaTable(idOrIds) {
  return request({
    url: '/datameta/meta-table/' + idOrIds,
    method: 'delete'
  })
}

export function listBusinessDatabases(data) {
  return request({
    url: '/datameta/business/databases',
    method: 'post',
    data: data
  })
}

export function listBusinessTables(data) {
  return request({
    url: '/datameta/business/tables',
    method: 'post',
    data: data
  })
}

export function listBusinessColumns(data) {
  return request({
    url: '/datameta/business/columns',
    method: 'post',
    data: data
  })
}
export function collectMeta(data) {
  return request({
    url: '/datameta/business/collect',
    method: 'post',
    data: data
  })
}

export function collectMetaTable(data) {
  return request({
    url: '/datameta/business/collect-table',
    method: 'post',
    data: data
  })
}


