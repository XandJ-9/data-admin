import request from '@/utils/request'

// 执行数据查询（请求体需包含 dataSourceId, sql, params, pageSize, offset）
export function executeQuery(data) {
  return request({
    url: '/dataservice/query',
    method: 'post',
    data: data
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