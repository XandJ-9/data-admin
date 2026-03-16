/**
 * 场景配置映射
 * 每个场景包含：
 * - taskType: 任务类型
 * - targetLayer: 目标层级
 * - executorType: 执行器类型
 * - defaultSyncMode: 默认同步方式
 * - requiredFields: 必填字段
 * - optionalFields: 可选字段
 * - defaults: 默认值
 */

export const SCENARIO_CONFIGS = {
  // 场景1: 业务库 → STG
  biz_to_stg: {
    taskType: 'dbToHive',
    targetLayer: 'stg',
    executorType: 'datax',
    defaultSyncMode: 'full',
    requiredFields: ['sourceDatasourceId', 'sourceTable'],
    optionalFields: ['whereCondition', 'batchSize', 'incrementalField'],
    defaults: {
      syncMode: 'full',
      batchSize: 10000,
      writeMode: 'overwrite',
      targetLayer: 'stg'
    },
    autoGenerateTarget: (sourceTable) => sourceTable,
    autoPartition: 'dt={{yyyyMMdd}}'
  },

  // 场景2: STG → ODS
  stg_to_ods: {
    taskType: 'hiveToHive',
    targetLayer: 'ods',
    executorType: 'spark_sql',
    defaultSyncMode: 'incremental',
    requiredFields: ['sourceTable'],
    optionalFields: ['transformRules', 'incrementalField'],
    defaults: {
      syncMode: 'incremental',
      batchSize: 50000,
      targetLayer: 'ods'
    },
    sqlTemplate: `
-- ODS层数据清洗和标准化
INSERT OVERWRITE TABLE {target_schema}.{target_table}
PARTITION (dt='{{yyyyMMdd}}')
SELECT
  {fields},
  CURRENT_TIMESTAMP AS load_time,
  '{{yyyyMMdd}}' AS data_date
FROM {source_schema}.{source_table}
WHERE {transform_rules}
  AND dt = '{{yyyyMMdd}}'
    `
  },

  // 场景3: 数仓计算
  warehouse_transform: {
    taskType: 'hiveToHive',
    targetLayer: 'dwd', // 用户选择
    executorType: 'spark_sql',
    defaultSyncMode: 'full',
    requiredFields: ['targetLayer', 'sqlScript'],
    optionalFields: ['scheduleCron'],
    defaults: {
      syncMode: 'full',
      scheduleType: 'scheduled',
      scheduleCron: '0 2 * * *'
    },
    validateSQL: true
  },

  // 场景4: 数仓 → 业务库
  warehouse_to_biz: {
    taskType: 'hiveToDb',
    targetLayer: 'ads',
    executorType: 'datax',
    defaultSyncMode: 'full',
    requiredFields: ['sourceTable', 'targetDatasourceId', 'targetTable'],
    optionalFields: ['batchSize', 'concurrency', 'writeMode'],
    defaults: {
      syncMode: 'full',
      batchSize: 10000,
      writeMode: 'overwrite',
      targetLayer: 'ads'
    }
  },

  // 场景5: 数据库互相同步
  db_to_db: {
    taskType: 'dbToDb',
    targetLayer: '',
    executorType: 'datax',
    defaultSyncMode: 'incremental',
    requiredFields: ['sourceDatasourceId', 'sourceTable', 'targetDatasourceId', 'targetTable'],
    optionalFields: ['whereCondition', 'incrementalField', 'batchSize'],
    defaults: {
      syncMode: 'incremental',
      batchSize: 10000
    }
  }
}

/**
 * 场景显示信息
 */
export const SCENARIO_INFO = {
  biz_to_stg: {
    title: '业务库 → STG层',
    description: '将业务系统数据库的数据同步到数仓STG缓冲层',
    icon: 'database',
    color: '#409EFF',
    tags: ['推荐新手', '全量同步']
  },
  stg_to_ods: {
    title: 'STG层 → ODS层',
    description: '对STG层数据进行清洗、标准化后同步到ODS原始层',
    icon: 'folder',
    color: '#67C23A',
    tags: ['数据标准化', '增量同步']
  },
  warehouse_transform: {
    title: '数仓层计算转换',
    description: '在DWD/DWS/ADS层使用Spark SQL进行复杂的数据聚合和计算',
    icon: 'data-analysis',
    color: '#F56C6C',
    tags: ['高级用户', 'SQL开发']
  },
  warehouse_to_biz: {
    title: '数仓层 → 业务库',
    description: '将数仓计算结果推送到业务数据库',
    icon: 'upload',
    color: '#E6A23C',
    tags: ['结果导出', '定时推送']
  },
  db_to_db: {
    title: '数据库互相同步',
    description: '在不同数据库之间同步数据，支持异构数据库',
    icon: 'switch',
    color: '#909399',
    tags: ['灵活配置', '数据迁移']
  }
}

/**
 * 获取场景配置
 */
export function getScenarioConfig(scenario) {
  return SCENARIO_CONFIGS[scenario] || {}
}

/**
 * 获取场景信息
 */
export function getScenarioInfo(scenario) {
  return SCENARIO_INFO[scenario] || {}
}

/**
 * 获取所有场景列表
 */
export function getAllScenarios() {
  return Object.keys(SCENARIO_CONFIGS)
}

/**
 * 根据数据源类型推荐合适的场景
 */
export function recommendScenario(sourceType, targetType) {
  // 如果目标是Hive
  if (targetType === 'hive') {
    if (sourceType === 'hive') {
      return 'stg_to_ods'
    } else {
      return 'biz_to_stg'
    }
  }

  // 如果目标是数据库
  if (sourceType === 'hive') {
    return 'warehouse_to_biz'
  }

  // 默认为库库同步
  return 'db_to_db'
}
