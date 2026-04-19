import axios from 'axios'
import request from '@/utils/request'
import { getToken } from '@/utils/auth'

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

// SQL查询：发布为数据接口
export function publishQueryAsInterface(data) {
  return request({
    url: '/dataservice/interface-info/publish',
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

// 接口信息：上线/下线
export function changeInterfaceStatus(interfaceId, enable) {
  return request({
    url: '/dataservice/interface-info/changeStatus',
    method: 'put',
    data: { interfaceId, enable }
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
export function testInterfaceById(interfaceId, data = {}) {
  return request({
    url: '/dataservice/interface-info/' + interfaceId + '/test',
    method: 'post',
    data: data
  })
}


// 接口：执行查询（按ID，返回对外接口协议）
export function executeInterfaceById(interfaceId, data) {
  const headers = { 'Content-Type': 'application/json;charset=utf-8' }
  const token = getToken()
  if (token) {
    headers.Authorization = 'Bearer ' + token
  }
  return axios({
    url: import.meta.env.VITE_APP_BASE_API + '/dataservice/interface-info/' + interfaceId + '/execute',
    method: 'post',
    data: data,
    timeout: 10000,
    headers,
  }).then(response => {
    const payload = response.data || {}
    if (payload.code !== '0') {
      const error = new Error(payload.message || '接口执行失败')
      error.msg = payload.message || '接口执行失败'
      return Promise.reject(error)
    }
    return payload
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

// 接口：导出接口定义（Excel）
export function exportInterfaceMeta(interfaceId) {
  return request({
    url: '/dataservice/interface-info/' + interfaceId + '/export-meta',
    method: 'post',
    responseType: 'blob'
  })
}

// 接口：导入接口定义（Excel）
export function importInterfaceMeta(data) {
  return request({
    url: '/dataservice/interface-info/import-meta',
    method: 'post',
    data: data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}