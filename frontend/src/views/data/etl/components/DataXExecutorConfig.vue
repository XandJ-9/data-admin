<template>
  <div class="datax-executor-config">
    <!-- DataX说明 -->
    <el-alert
      title="DataX执行器"
      type="success"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    >
      DataX是阿里开源的离线数据同步工具，支持多种异构数据源之间的高效数据同步。
      <a href="https://github.com/alibaba/DataX" target="_blank">查看文档</a>
    </el-alert>

    <!-- DataX Reader配置 -->
    <el-card shadow="never" class="config-card">
      <template #header>
        <span>DataX Reader配置（源端）</span>
      </template>

      <el-form :model="dataxConfig.reader" label-width="140px">
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="字段列表">
              <el-input
                v-model="readerFieldsStr"
                type="textarea"
                :rows="3"
                placeholder="请输入字段列表，用逗号分隔，如：id,user_name,email,phone"
              />
              <div class="form-item-tip">
                <el-text size="small" type="info">
                  要同步的源表字段列表，多个字段用逗号分隔。留空表示同步所有字段（*）
                </el-text>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="24" v-if="form.etlType === 'extract'">
            <el-form-item label="查询SQL">
              <el-input
                v-model="dataxConfig.reader.querySql"
                type="textarea"
                :rows="4"
                placeholder="自定义查询SQL，如：SELECT * FROM user_info WHERE update_time >= '{{last_sync_time}}'"
              />
              <div class="form-item-tip">
                <el-text size="small" type="warning">
                  自定义SQL将与字段列表二选一，优先使用自定义SQL
                </el-text>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 字段映射配置 -->
    <el-card shadow="never" class="config-card">
      <template #header>
        <div class="card-header">
          <span>字段映射配置</span>
          <el-button size="small" type="primary" icon="Plus" @click="addFieldMapping">添加映射</el-button>
        </div>
      </template>

      <div class="field-mapping-container">
        <!-- 字段映射列表 -->
        <div class="mapping-list" v-if="fieldMappings.length > 0">
          <div class="mapping-item" v-for="(mapping, index) in fieldMappings" :key="index">
            <div class="mapping-source">
              <el-input
                v-model="mapping.sourceField"
                placeholder="源表字段"
                size="small"
                clearable
              />
            </div>
            <div class="mapping-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
            <div class="mapping-target">
              <el-input
                v-model="mapping.targetField"
                placeholder="目标表字段"
                size="small"
                clearable
              />
            </div>
            <div class="mapping-actions">
              <el-button
                size="small"
                type="danger"
                icon="Delete"
                link
                @click="removeFieldMapping(index)"
              />
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty
          v-else
          description="暂无字段映射，点击右上角添加"
          :image-size="80"
        />

        <!-- 快速填充说明 -->
        <el-alert
          title="使用提示"
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 16px"
        >
          <ul class="mapping-tips">
            <li>如果源表和目标表字段名相同，可以只配置源表字段，系统会自动映射</li>
            <li>留空表示映射所有字段（*），按字段名自动匹配</li>
            <li>支持字段重命名：源表字段 → 目标表字段</li>
          </ul>
        </el-alert>

        <!-- 批量输入 -->
        <el-collapse style="margin-top: 16px">
          <el-collapse-item title="批量输入字段映射（高级）" name="batch">
            <el-form label-width="100px">
              <el-form-item label="源表字段">
                <el-input
                  v-model="batchSourceFields"
                  type="textarea"
                  :rows="3"
                  placeholder="每行一个字段名，如：&#10;id&#10;user_name&#10;email"
                />
              </el-form-item>
              <el-form-item label="目标表字段">
                <el-input
                  v-model="batchTargetFields"
                  type="textarea"
                  :rows="3"
                  placeholder="每行一个字段名，与源表字段一一对应&#10;user_id&#10;username&#10;email_address"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="batchImportMappings">批量导入</el-button>
                <el-button @click="clearBatchFields">清空</el-button>
              </el-form-item>
            </el-form>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>

    <!-- DataX Writer配置 -->
    <el-card shadow="never" class="config-card">
      <template #header>
        <span>DataX Writer配置（目标端）</span>
      </template>

      <el-form :model="dataxConfig.writer" label-width="140px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="写入模式">
              <el-select v-model="dataxConfig.writer.writeMode" placeholder="请选择写入模式" style="width: 100%">
                <el-option label="追加（append）" value="append" />
                <el-option label="覆盖（overwrite）" value="overwrite" />
                <el-option label="非冲突覆盖（nonConflict）" value="nonConflict" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="文件类型">
              <el-select v-model="dataxConfig.writer.fileType" placeholder="请选择文件类型" style="width: 100%">
                <el-option label="文本（text）" value="text" />
                <el-option label="ORC" value="orc" />
                <el-option label="Parquet" value="parquet" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="字段分隔符">
              <el-input
                v-model="dataxConfig.writer.fieldDelimiter"
                placeholder="默认: , (逗号)"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="压缩格式">
              <el-select v-model="dataxConfig.writer.compress" placeholder="请选择压缩格式" style="width: 100%">
                <el-option label="GZIP" value="gzip" />
                <el-option label="ZIP" value="zip" />
                <el-option label="SNAPPY" value="snappy" />
                <el-option label="LZO" value="lzo" />
                <el-option label="不压缩" value="none" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 速度与并发配置 -->
    <el-card shadow="never" class="config-card">
      <template #header>
        <span>速度与并发配置</span>
      </template>

      <el-form :model="dataxConfig.speed" label-width="140px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="并发通道数">
              <el-input-number
                v-model="dataxConfig.speed.channel"
                :min="1"
                :max="10"
                placeholder="通道数"
                style="width: 100%"
              />
              <div class="form-item-tip">
                <el-text size="small" type="info">并发同步通道数（1-10）</el-text>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="字节限速">
              <el-input-number
                v-model="dataxConfig.speed.byte"
                :min="0"
                :step="1048576"
                :precision="0"
                placeholder="字节/秒"
                style="width: 100%"
              />
              <div class="form-item-tip">
                <el-text size="small" type="info">
                  {{ formatBytes(dataxConfig.speed.byte) }}/s
                </el-text>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="记录限速">
              <el-input-number
                v-model="dataxConfig.speed.record"
                :min="0"
                :step="10000"
                :precision="0"
                placeholder="记录/秒"
                style="width: 100%"
              />
              <div class="form-item-tip">
                <el-text size="small" type="info">{{ formatNumber(dataxConfig.speed.record) }} 记录/s</el-text>
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">性能建议</el-divider>

        <el-alert
          title="根据网络和数据库负载调整"
          type="success"
          :closable="false"
          show-icon
        >
          <ul class="performance-tips">
            <li>千兆网络：建议 channel=1-3, byte=1048576 (1MB/s)</li>
            <li>万兆网络：建议 channel=3-5, byte=10485760 (10MB/s)</li>
            <li>限制磁盘I/O：降低 byte 和 record 值</li>
            <li>初次运行：建议使用较小值测试</li>
          </ul>
        </el-alert>
      </el-form>
    </el-card>

    <!-- 增量策略配置 -->
    <el-card shadow="never" class="config-card" v-if="form.executeStrategy === 'increment'">
      <template #header>
        <div class="card-header">
          <span>增量策略配置</span>
          <el-switch
            v-model="incrementalConfig.enabled"
            active-text="启用"
            inactive-text="禁用"
            @change="handleIncrementalEnabledChange"
          />
        </div>
      </template>

      <el-form :model="incrementalConfig" label-width="120px" v-show="incrementalConfig.enabled">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="增量字段">
              <el-input
                v-model="incrementalConfig.field"
                placeholder="请输入增量字段名，如：update_time、id"
                clearable
              >
                <template #prepend>
                  <el-icon><Clock /></el-icon>
                </template>
              </el-input>
              <div class="form-item-tip">
                <el-text size="small" type="info">用于增量抽取的字段名</el-text>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="增量策略类型">
              <el-select v-model="incrementalConfig.strategy" placeholder="请选择增量策略类型" style="width: 100%">
                <el-option label="时间戳" value="timestamp" />
                <el-option label="自增ID" value="id" />
                <el-option label="变更数据捕获（CDC）" value="cdc" />
              </el-select>
              <div class="form-item-tip">
                <el-text size="small" type="info">
                  {{ getStrategyDescription(incrementalConfig.strategy) }}
                </el-text>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 多租户配置 -->
    <el-card shadow="never" class="config-card" v-if="form.etlType === 'extract'">
      <template #header>
        <div class="card-header">
          <span>多租户配置（STG任务）</span>
          <el-switch
            v-model="multiTenantConfig.enabled"
            active-text="启用"
            inactive-text="禁用"
            @change="handleMultiTenantEnabledChange"
          />
        </div>
      </template>

      <el-alert
        title="多租户配置说明"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        启用后，系统将为每个租户的数据源创建独立的STG采集任务，数据将按租户分区存储
      </el-alert>

      <el-form :model="multiTenantConfig" label-width="140px" v-show="multiTenantConfig.enabled">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="租户ID字段名">
              <el-input
                v-model="multiTenantConfig.tenant_id_field"
                placeholder="请输入租户ID字段名，如：tenant_id"
                clearable
              >
                <template #prepend>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
              <div class="form-item-tip">
                <el-text size="small" type="info">源表中用于标识租户的字段名</el-text>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="当前租户">
              <el-input
                v-model="multiTenantConfig.tenant_id"
                placeholder="请输入当前租户标识"
                clearable
              >
                <template #prepend>
                  <el-icon><OfficeBuilding /></el-icon>
                </template>
              </el-input>
              <div class="form-item-tip">
                <el-text size="small" type="info">用于标识当前租户的唯一标识</el-text>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="租户数据源列表">
              <el-select
                v-model="multiTenantConfig.tenant_source_ids"
                multiple
                filterable
                placeholder="请选择租户对应的数据源"
                style="width: 100%"
              >
                <el-option
                  v-for="ds in datasourceOptions"
                  :key="ds.dataSourceId"
                  :label="ds.dataSourceName"
                  :value="ds.dataSourceId"
                />
              </el-select>
              <div class="form-item-tip">
                <el-text size="small" type="info">
                  多租户场景下，每个租户的数据源ID列表（高级配置）
                </el-text>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Clock, User, OfficeBuilding, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  form: {
    type: Object,
    required: true
  },
  datasourceOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

// 批量输入字段
const batchSourceFields = ref('')
const batchTargetFields = ref('')

const dataxConfig = computed({
  get: () => {
    const config = props.modelValue || {}
    return {
      reader: config.reader || {},
      writer: config.writer || {},
      speed: config.speed || {},
      ...config
    }
  },
  set: (val) => emit('update:modelValue', val)
})

// 字段映射列表
const fieldMappings = computed({
  get: () => {
    return dataxConfig.value.fieldMappings || []
  },
  set: (val) => {
    dataxConfig.value = { ...dataxConfig.value, fieldMappings: val }
  }
})

// 增量配置
const incrementalConfig = computed({
  get: () => {
    return props.form.executorParams?.incremental || {
      enabled: false,
      field: '',
      strategy: 'timestamp'
    }
  },
  set: (val) => {
    const newParams = { ...props.form.executorParams }
    newParams.incremental = val
    props.form.executorParams = newParams
  }
})

// 多租户配置
const multiTenantConfig = computed({
  get: () => {
    return props.form.executorParams?.multi_tenant || {
      enabled: false,
      tenant_id_field: '',
      tenant_id: '',
      tenant_source_ids: []
    }
  },
  set: (val) => {
    const newParams = { ...props.form.executorParams }
    newParams.multi_tenant = val
    props.form.executorParams = newParams
  }
})

// 字段列表字符串
const readerFieldsStr = computed({
  get: () => {
    const fields = dataxConfig.value.reader?.column || []
    return Array.isArray(fields) ? fields.join(', ') : fields
  },
  set: (val) => {
    const fields = val ? val.split(',').map(f => f.trim()).filter(f => f) : []
    const newReader = { ...dataxConfig.value.reader, column: fields }
    dataxConfig.value = { ...dataxConfig.value, reader: newReader }
  }
})

// 添加字段映射
function addFieldMapping() {
  const mappings = [...fieldMappings.value]
  mappings.push({
    sourceField: '',
    targetField: ''
  })
  fieldMappings.value = mappings
}

// 删除字段映射
function removeFieldMapping(index) {
  const mappings = [...fieldMappings.value]
  mappings.splice(index, 1)
  fieldMappings.value = mappings
}

// 批量导入字段映射
function batchImportMappings() {
  const sourceFields = batchSourceFields.value
    .split('\n')
    .map(f => f.trim())
    .filter(f => f)

  const targetFields = batchTargetFields.value
    .split('\n')
    .map(f => f.trim())
    .filter(f => f)

  if (sourceFields.length === 0) {
    return
  }

  const maxLength = Math.max(sourceFields.length, targetFields.length)
  const newMappings = []

  for (let i = 0; i < maxLength; i++) {
    newMappings.push({
      sourceField: sourceFields[i] || '',
      targetField: targetFields[i] || ''
    })
  }

  fieldMappings.value = [...fieldMappings.value, ...newMappings]
  clearBatchFields()
}

// 清空批量输入
function clearBatchFields() {
  batchSourceFields.value = ''
  batchTargetFields.value = ''
}

// 格式化字节
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 格式化数字
const formatNumber = (num) => {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 增量策略描述
const getStrategyDescription = (strategy) => {
  const descriptions = {
    timestamp: '基于时间戳字段进行增量抽取（如：update_time >= 上次时间）',
    id: '基于自增ID字段进行增量抽取（如：id > 上次最大ID）',
    cdc: '基于变更数据捕获进行增量抽取（需要数据库支持CDC）'
  }
  return descriptions[strategy] || ''
}

// 增量配置启用/禁用处理
const handleIncrementalEnabledChange = (enabled) => {
  if (!enabled) {
    incrementalConfig.value = {
      enabled: false,
      field: '',
      strategy: 'timestamp'
    }
  }
}

// 多租户配置启用/禁用处理
const handleMultiTenantEnabledChange = (enabled) => {
  if (!enabled) {
    multiTenantConfig.value = {
      enabled: false,
      tenant_id_field: '',
      tenant_id: '',
      tenant_source_ids: []
    }
  }
}
</script>

<style scoped>
.datax-executor-config {
  padding: 10px 0;
}

.config-card {
  margin-bottom: 20px;
}

.form-item-tip {
  margin-top: 5px;
  line-height: 1.4;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.performance-tips {
  margin: 10px 0 0 0;
  padding-left: 20px;
  line-height: 1.8;
}

.performance-tips li {
  margin-bottom: 5px;
}

/* 字段映射样式 */
.field-mapping-container {
  padding: 10px 0;
}

.mapping-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mapping-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  transition: all 0.3s;
}

.mapping-item:hover {
  background: #ecf5ff;
}

.mapping-source,
.mapping-target {
  flex: 1;
  min-width: 0;
}

.mapping-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #fff;
  border-radius: 50%;
  color: #409eff;
  font-size: 18px;
}

.mapping-actions {
  display: flex;
  align-items: center;
}

.mapping-tips {
  margin: 10px 0 0 0;
  padding-left: 20px;
  line-height: 1.8;
}

.mapping-tips li {
  margin-bottom: 5px;
}
</style>
