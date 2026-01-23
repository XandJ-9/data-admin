/**
 * ETL场景组件统一导出
 * 每个场景封装为一个独立组件，便于维护和复用
 */

import BizToStgScenario from './BizToStgScenario.vue'
import StgToOdsScenario from './StgToOdsScenario.vue'
import WarehouseTransformScenario from './WarehouseTransformScenario.vue'
import WarehouseToBizScenario from './WarehouseToBizScenario.vue'
import DbToDbScenario from './DbToDbScenario.vue'

/**
 * 场景组件映射表
 * key: 场景标识符
 * value: 对应的Vue组件
 */
export const SCENARIO_COMPONENTS = {
  biz_to_stg: BizToStgScenario,
  stg_to_ods: StgToOdsScenario,
  warehouse_transform: WarehouseTransformScenario,
  warehouse_to_biz: WarehouseToBizScenario,
  db_to_db: DbToDbScenario
}

/**
 * 场景配置信息
 */
export const SCENARIO_INFO = {
  biz_to_stg: {
    name: '业务库 → STG',
    description: '将业务库数据同步到数据仓库STG层',
    component: BizToStgScenario,
    steps: ['选择业务库和表', '配置字段映射', '设置同步方式'],
    skipMapping: false
  },
  stg_to_ods: {
    name: 'STG → ODS',
    description: '将STG层数据清洗后同步到ODS层',
    component: StgToOdsScenario,
    steps: ['选择STG表', '配置清洗规则和映射', '设置同步方式'],
    skipMapping: false
  },
  warehouse_transform: {
    name: '数仓计算',
    description: '通过SQL计算生成DWD/DWS/ADS层表',
    component: WarehouseTransformScenario,
    steps: ['编写计算SQL', '配置输出字段', '设置执行计划'],
    skipMapping: true // 数仓计算场景跳过字段映射步骤
  },
  warehouse_to_biz: {
    name: '数仓 → 业务库',
    description: '将数仓结果导出到业务库',
    component: WarehouseToBizScenario,
    steps: ['选择数仓表和目标库', '配置字段映射', '设置执行方式'],
    skipMapping: false
  },
  db_to_db: {
    name: '库库同步',
    description: '数据库之间的数据同步',
    component: DbToDbScenario,
    steps: ['选择源库和目标库', '配置字段映射', '设置同步方式'],
    skipMapping: false
  }
}

/**
 * 根据场景标识获取组件
 * @param {string} scenario - 场景标识符
 * @returns {Component|null} 对应的场景组件，如果不存在则返回null
 */
export function getScenarioComponent(scenario) {
  return SCENARIO_COMPONENTS[scenario] || null
}

/**
 * 根据场景标识获取场景信息
 * @param {string} scenario - 场景标识符
 * @returns {Object|null} 对应的场景信息，如果不存在则返回null
 */
export function getScenarioInfo(scenario) {
  return SCENARIO_INFO[scenario] || null
}

/**
 * 获取所有可用的场景列表
 * @returns {Array} 场景列表
 */
export function getAllScenarios() {
  return Object.keys(SCENARIO_COMPONENTS).map(key => ({
    key,
    ...SCENARIO_INFO[key]
  }))
}

// 默认导出所有组件
export default {
  BizToStgScenario,
  StgToOdsScenario,
  WarehouseTransformScenario,
  WarehouseToBizScenario,
  DbToDbScenario
}
