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

export function collectMeta(dataSourceId) {
  return request({
    url: '/datameta/meta-table/collect',
    method: 'post',
    data: { dataSourceId }
  })
}

export function listBusinessTables(query) {
  return request({
    url: '/datameta/business/tables',
    method: 'get',
    params: query
  })
}

export function listBusinessColumns(query) {
  return request({
    url: '/datameta/business/columns',
    method: 'get',
    params: query
  })
}

export function collectMetaTable(dataSourceId, tableName) {
  return request({
    url: '/datameta/meta-table/collect-table',
    method: 'post',
    data: { dataSourceId, tableName }
  })
}

export function listDatabases(query) {
  return request({
    url: '/datameta/business/databases',
    method: 'get',
    params: query
  })
}
