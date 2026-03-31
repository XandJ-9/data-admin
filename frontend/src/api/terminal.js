/**
 * Terminal API Wrapper
 * Handles session and command management via REST API
 */
import request from '@/utils/request'

export const terminalApi = {
  /**
   * Create a new terminal session
   */
  createSession(data) {
    return request({
      url: '/terminal/session/',
      method: 'post',
      data
    })
  },

  /**
   * List terminal sessions
   */
  listSessions(query) {
    return request({
      url: '/terminal/session/',
      method: 'get',
      params: query
    })
  },

  /**
   * Get active terminal sessions
   */
  getActiveSessions(query) {
    return request({
      url: '/terminal/session/active/',
      method: 'get',
      params: query
    })
  },

  /**
   * Close a terminal session
   */
  closeSession(sessionId) {
    return request({
      url: `/terminal/session/${sessionId}/close/`,
      method: 'post'
    })
  },

  /**
   * Get command history for a session
   */
  getCommandHistory(sessionId, query) {
    return request({
      url: `/terminal/session/${sessionId}/commands/`,
      method: 'get',
      params: query
    })
  },

  /**
   * Get recent commands for current user
   */
  getRecentCommands(query) {
    return request({
      url: '/terminal/command/recent/',
      method: 'get',
      params: query
    })
  },

  /**
   * Search commands by keyword
   */
  searchCommands(keyword, query = {}) {
    return request({
      url: '/terminal/command/search/',
      method: 'post',
      data: { keyword, ...query }
    })
  }
}

export default terminalApi
