<template>
  <div class="data-mapping-tab">
    <!-- 翻转切换按钮 -->
    <div class="mapping-header">
      <div class="mapping-actions" v-if="isEdit && !flipped">
        <el-button type="primary" icon="Plus" size="small" @click="handleAddMapping">
          添加映射
        </el-button>
        <el-button type="success" icon="MagicStick" size="small" @click="handleAutoMapping">
          自动映射
        </el-button>
        <el-button type="warning" icon="Delete" size="small" @click="handleClearMapping">
          清空映射
        </el-button>
      </div>
      <div v-else />
      <el-button
        :icon="flipped ? 'Grid' : 'Document'"
        size="small"
        @click="flipped = !flipped"
      >
        {{ flipped ? '切换到映射' : '切换到SQL' }}
      </el-button>
    </div>

    <!-- 翻转面板 -->
    <FlipCard :flipped="flipped" min-height="350px">
      <template #front>
        <el-table :data="fieldMappings" border stripe max-height="400">
          <el-table-column prop="sourceFieldName" label="源字段" min-width="150">
            <template #default="{ row }">
              <el-select
                v-if="isEdit"
                v-model="row.sourceFieldName"
                placeholder="选择源字段"
                filterable
                allow-create
                @change="(val) => handleSourceFieldSelect(row, val)"
              >
                <el-option
                  v-for="col in sourceColumns"
                  :key="col.name"
                  :label="col.name"
                  :value="col.name"
                />
              </el-select>
              <span v-else>{{ row.sourceFieldName }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="targetFieldName" label="目标字段" min-width="150">
            <template #default="{ row }">
              <el-input v-if="isEdit" v-model="row.targetFieldName" placeholder="目标字段名" />
              <span v-else>{{ row.targetFieldName }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="dataType" label="数据类型" width="130">
            <template #default="{ row }">
              <el-select v-if="isEdit" v-model="row.dataType" placeholder="数据类型">
                <el-option label="STRING" value="string" />
                <el-option label="INTEGER" value="integer" />
                <el-option label="LONG" value="long" />
                <el-option label="DOUBLE" value="double" />
                <el-option label="DECIMAL" value="decimal" />
                <el-option label="DATE" value="date" />
                <el-option label="DATETIME" value="datetime" />
                <el-option label="BOOLEAN" value="boolean" />
              </el-select>
              <span v-else>{{ row.dataType }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="transformRule" label="转换规则" min-width="150">
            <template #default="{ row }">
              <el-input v-if="isEdit" v-model="row.transformRule" placeholder="转换规则" />
              <span v-else>{{ row.transformRule || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="isPrimaryKey" label="主键" width="70" align="center">
            <template #default="{ row }">
              <el-checkbox v-if="isEdit" v-model="row.isPrimaryKey" />
              <el-tag v-else-if="row.isPrimaryKey" type="success" size="small">是</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column v-if="isEdit" label="操作" width="70" align="center" fixed="right">
            <template #default="{ $index }">
              <el-button link type="danger" icon="Delete" @click="handleDeleteMapping($index)" />
            </template>
          </el-table-column>
        </el-table>
      </template>

      <template #back>
        <div class="sql-config">
          <div class="sql-header">
            <span>SQL配置内容</span>
            <el-button v-if="isEdit" type="primary" size="small" @click="handleFormatSQL">
              格式化SQL
            </el-button>
          </div>
          <el-input
            v-model="form.sqlConfig"
            type="textarea"
            :rows="16"
            placeholder="请输入SQL配置，支持采集SQL、转换SQL、加载SQL等"
            :disabled="!isEdit"
          />
        </div>
      </template>
    </FlipCard>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FlipCard from '@/components/FlipCard/index.vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  form: { type: Object, required: true },
  isEdit: { type: Boolean, default: false },
  sourceColumns: { type: Array, default: () => [] },
  fieldMappings: { type: Array, required: true }
})

const emit = defineEmits(['update:fieldMappings'])

const flipped = ref(false)

// 数据类型映射：将数据库类型映射为通用类型
function mapDbTypeToGeneric(dbType) {
  if (!dbType) return 'string'
  const t = dbType.toLowerCase()
  if (t.includes('int')) return 'integer'
  if (t.includes('bigint')) return 'long'
  if (t.includes('double') || t.includes('float')) return 'double'
  if (t.includes('decimal') || t.includes('numeric')) return 'decimal'
  if (t.includes('datetime') || t.includes('timestamp')) return 'datetime'
  if (t.includes('date')) return 'date'
  if (t.includes('bool') || t.includes('bit')) return 'boolean'
  return 'string'
}

function handleSourceFieldSelect(row, fieldName) {
  const col = props.sourceColumns.find(c => c.name === fieldName)
  if (col) {
    if (!row.targetFieldName) row.targetFieldName = col.name
    row.dataType = mapDbTypeToGeneric(col.type)
    row.isPrimaryKey = !!col.primary
  }
}

function handleAddMapping() {
  props.fieldMappings.push({
    sourceFieldName: '',
    targetFieldName: '',
    dataType: 'string',
    transformRule: '',
    isPrimaryKey: false
  })
}

function handleAutoMapping() {
  if (props.sourceColumns.length === 0) {
    ElMessage.warning('请先在数据源配置中选择源表')
    return
  }
  // 清空现有映射，基于源字段1:1生成
  props.fieldMappings.splice(0, props.fieldMappings.length)
  props.sourceColumns.forEach(col => {
    props.fieldMappings.push({
      sourceFieldName: col.name,
      targetFieldName: col.name,
      dataType: mapDbTypeToGeneric(col.type),
      transformRule: '',
      isPrimaryKey: !!col.primary
    })
  })
  ElMessage.success(`已自动映射 ${props.sourceColumns.length} 个字段`)
}

function handleClearMapping() {
  props.fieldMappings.splice(0, props.fieldMappings.length)
}

function handleDeleteMapping(index) {
  props.fieldMappings.splice(index, 1)
}

function handleFormatSQL() {
  // 简单的SQL格式化
  if (props.form.sqlConfig) {
    props.form.sqlConfig = props.form.sqlConfig
      .replace(/\s+/g, ' ')
      .replace(/\s*,\s*/g, ',\n  ')
      .replace(/\bSELECT\b/gi, 'SELECT\n  ')
      .replace(/\bFROM\b/gi, '\nFROM')
      .replace(/\bWHERE\b/gi, '\nWHERE')
      .replace(/\bAND\b/gi, '\n  AND')
      .replace(/\bOR\b/gi, '\n  OR')
      .replace(/\bORDER BY\b/gi, '\nORDER BY')
      .replace(/\bGROUP BY\b/gi, '\nGROUP BY')
      .replace(/\bJOIN\b/gi, '\nJOIN')
      .replace(/\bLEFT\b/gi, '\nLEFT')
      .replace(/\bRIGHT\b/gi, '\nRIGHT')
      .replace(/\bINNER\b/gi, '\nINNER')
      .trim()
  }
}
</script>

<style scoped lang="scss">
.data-mapping-tab {
  .mapping-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .sql-config {
    .sql-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
  }
}
</style>
