<template>
  <div class="transform-step">
    <el-alert
      title="转换与映射配置"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 24px"
    >
      根据任务类型配置字段映射关系或SQL转换脚本
    </el-alert>

    <!-- 数据集成类型 - 字段映射 -->
    <template v-if="etlType === 'data_integration'">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>字段映射配置</span>
            <div class="header-actions">
              <el-button :icon="Refresh" @click="loadSourceFields">
                刷新字段
              </el-button>
              <el-button type="primary" :icon="MagicStick" @click="handleAutoMap">
                智能映射
              </el-button>
            </div>
          </div>
        </template>

        <!-- 字段映射编辑器 -->
        <FieldMappingEditor
          ref="fieldMappingRef"
          v-model:source-columns="formData.sourceColumns"
          v-model:target-columns="formData.targetColumns"
          v-model:mappings="formData.fieldMappings"
          :readonly="!formData.sourceColumns || formData.sourceColumns.length === 0"
        />

        <!-- 数据预览对比 -->
        <el-divider content-position="left">映射预览</el-divider>
        <div class="mapping-preview">
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="preview-panel">
                <div class="panel-header">
                  <el-icon><Download /></el-icon>
                  <span>源字段</span>
                  <el-tag size="small">{{ formData.sourceColumns?.length || 0 }} 个字段</el-tag>
                </div>
                <div class="panel-content">
                  <el-tag
                    v-for="col in formData.sourceColumns"
                    :key="col"
                    closable
                    @close="handleRemoveSourceColumn(col)"
                  >
                    {{ col }}
                  </el-tag>
                  <el-empty v-if="!formData.sourceColumns?.length" description="暂无源字段" :image-size="60" />
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="preview-panel">
                <div class="panel-header">
                  <el-icon><Upload /></el-icon>
                  <span>目标字段</span>
                  <el-tag size="small">{{ formData.targetColumns?.length || 0 }} 个字段</el-tag>
                </div>
                <div class="panel-content">
                  <el-tag
                    v-for="col in formData.targetColumns"
                    :key="col"
                    closable
                    @close="handleRemoveTargetColumn(col)"
                  >
                    {{ col }}
                  </el-tag>
                  <el-empty v-if="!formData.targetColumns?.length" description="暂无目标字段" :image-size="60" />
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 转换规则 -->
        <el-divider content-position="left">转换规则</el-divider>
        <el-form label-width="120px">
          <el-form-item label="数据过滤">
            <el-input
              v-model="formData.transformRules"
              type="textarea"
              :rows="3"
              placeholder="可选：输入WHERE条件，例如：status = 1 AND amount > 0"
            />
            <div class="form-tip">
              <el-icon><QuestionFilled /></el-icon>
              在数据抽取前应用过滤条件，只同步符合条件的数据
            </div>
          </el-form-item>
        </el-form>
      </el-card>
    </template>

    <!-- SQL任务类型 - SQL脚本 -->
    <template v-else-if="etlType === 'sql_task'">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>SQL转换脚本</span>
            <div class="header-actions">
              <el-button :icon="Document" @click="handleShowTemplates">
                模板
              </el-button>
              <el-button :icon="MagicStick" @click="handleFormatSql">
                格式化
              </el-button>
              <el-button type="primary" :icon="VideoPlay" @click="handleExecuteSql">
                试运行
              </el-button>
            </div>
          </div>
        </template>

        <!-- SQL编辑器 -->
        <div class="sql-editor-container">
          <SqlEditor
            ref="sqlEditorRef"
            v-model="formData.sqlScript"
            language="sparksql"
            :height="500"
            placeholder="请输入Spark SQL脚本，例如：&#10;INSERT INTO target_table&#10;SELECT&#10;  user_id,&#10;  SUM(amount) as total_amount&#10;FROM orders&#10;WHERE dt = '${biz_date}'&#10;GROUP BY user_id"
            @change="handleSqlChange"
          />
        </div>

        <!-- 变量说明 -->
        <el-collapse style="margin-top: 16px">
          <el-collapse-item name="variables" title="可用变量">
            <el-table :data="sqlVariables" border size="small">
              <el-table-column prop="name" label="变量名" width="200" />
              <el-table-column prop="description" label="说明" />
              <el-table-column prop="example" label="示例值" width="200" />
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <!-- 输出字段配置 -->
      <el-card shadow="never" style="margin-top: 16px">
        <template #header>
          <span>输出字段配置</span>
        </template>

        <el-form label-width="120px">
          <el-form-item label="字段定义">
            <el-input
              v-model="outputFieldsDefinition"
              type="textarea"
              :rows="6"
              placeholder="定义输出字段，格式：字段名 类型 描述&#10;例如：&#10;user_id BIGINT 用户ID&#10;total_amount DECIMAL(10,2) 总金额&#10;order_count INT 订单数"
            />
            <div class="form-tip">
              <el-icon><QuestionFilled /></el-icon>
              定义SQL脚本的输出字段结构，用于自动创建目标表
            </div>
          </el-form-item>

          <el-form-item label="自动解析">
            <el-button :icon="MagicStick" @click="handleParseOutputFields">
              从SQL解析字段
            </el-button>
            <span v-if="parsedFields.length > 0" class="parsed-info">
              已解析 {{ parsedFields.length }} 个字段
            </span>
          </el-form-item>
        </el-form>

        <!-- 解析结果 -->
        <el-table
          v-if="parsedFields.length > 0"
          :data="parsedFields"
          border
          size="small"
          max-height="300"
        >
          <el-table-column prop="name" label="字段名" width="180" />
          <el-table-column prop="type" label="类型" width="150" />
          <el-table-column prop="comment" label="说明" />
        </el-table>
      </el-card>
    </template>

    <!-- 字段映射模板选择对话框 -->
    <el-dialog
      v-model="templateDialogVisible"
      title="SQL模板"
      width="800px"
      append-to-body
    >
      <el-tabs v-model="activeTemplateTab">
        <el-tab-pane
          v-for="category in sqlTemplates"
          :key="category.name"
          :label="category.label"
          :name="category.name"
        >
          <el-card
            v-for="template in category.templates"
            :key="template.name"
            class="template-card"
            shadow="hover"
            @click="handleUseTemplate(template)"
          >
            <div class="template-header">
              <span class="template-name">{{ template.name }}</span>
              <el-button size="small" type="primary">使用</el-button>
            </div>
            <div class="template-desc">{{ template.description }}</div>
            <pre class="template-code">{{ template.code }}</pre>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  Refresh,
  MagicStick,
  Download,
  Upload,
  VideoPlay,
  Document,
  QuestionFilled
} from '@element-plus/icons-vue'
import FieldMappingEditor from '../components/FieldMappingEditor.vue'
import SqlEditor from '../components/SqlEditor.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  etlType: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const fieldMappingRef = ref()
const sqlEditorRef = ref()
const templateDialogVisible = ref(false)
const activeTemplateTab = ref('common')
const outputFieldsDefinition = ref('')
const parsedFields = ref([])

const formData = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// SQL变量列表
const sqlVariables = ref([
  { name: '${biz_date}', description: '业务日期，格式：YYYY-MM-DD', example: '2024-01-15' },
  { name: '${biz_date_prev}', description: '前一天业务日期', example: '2024-01-14' },
  { name: '${last_run_time}', description: '上次运行时间', example: '2024-01-15 10:00:00' },
  { name: '${current_time}', description: '当前时间', example: '2024-01-15 11:00:00' }
])

// SQL模板
const sqlTemplates = ref([
  {
    name: 'common',
    label: '常用模板',
    templates: [
      {
        name: '全量同步',
        description: '将源表全量数据同步到目标表',
        code: `INSERT OVERWRITE TABLE target_table
SELECT
  col1,
  col2,
  col3
FROM source_table
WHERE dt = '${biz_date}';`
      },
      {
        name: '增量同步',
        description: '基于时间戳的增量数据同步',
        code: `INSERT INTO target_table
SELECT
  col1,
  col2,
  col3
FROM source_table
WHERE updated_time > '${last_run_time}'
  AND dt = '${biz_date}';`
      }
    ]
  },
  {
    name: 'aggregate',
    label: '聚合统计',
    templates: [
      {
        name: '用户日汇总',
        description: '按用户维度统计日指标',
        code: `INSERT OVERWRITE TABLE dwd_user_daily_summary
SELECT
  user_id,
  COUNT(order_id) as order_count,
  SUM(amount) as total_amount,
  '${biz_date}' as biz_date
FROM orders
WHERE dt = '${biz_date}'
GROUP BY user_id;`
      },
      {
        name: '商品销售排行',
        description: '计算商品销售排行榜',
        code: `INSERT OVERWRITE TABLE dws_product_ranking
SELECT
  product_id,
  product_name,
  SUM(sales_amount) as total_sales,
  RANK() OVER (ORDER BY SUM(sales_amount) DESC) as ranking
FROM order_items
WHERE dt = '${biz_date}'
GROUP BY product_id, product_name;`
      }
    ]
  }
])

// 方法
function loadSourceFields() {
  // TODO: 重新加载源字段
  console.log('Refresh source fields')
}

function handleAutoMap() {
  fieldMappingRef.value?.autoMap()
}

function handleRemoveSourceColumn(col) {
  const index = formData.value.sourceColumns?.indexOf(col)
  if (index > -1) {
    formData.value.sourceColumns.splice(index, 1)
  }
}

function handleRemoveTargetColumn(col) {
  const index = formData.value.targetColumns?.indexOf(col)
  if (index > -1) {
    formData.value.targetColumns.splice(index, 1)
  }
}

function handleFormatSql() {
  // TODO: SQL格式化
  console.log('Format SQL')
}

function handleExecuteSql() {
  // TODO: 试运行SQL
  console.log('Execute SQL')
}

function handleSqlChange(sql) {
  formData.value.sqlScript = sql
  // 自动解析输出字段
  if (sql) {
    parseOutputFields()
  }
}

function handleShowTemplates() {
  templateDialogVisible.value = true
}

function handleUseTemplate(template) {
  formData.value.sqlScript = template.code
  templateDialogVisible.value = false
}

function handleParseOutputFields() {
  parseOutputFields()
}

function parseOutputFields() {
  const sql = formData.value.sqlScript || ''
  // TODO: 解析SQL提取输出字段
  // 这里使用简单的正则匹配，实际应该使用SQL解析器

  const matches = sql.match(/SELECT\s+([\s\S]+?)\s+FROM/i)
  if (matches && matches[1]) {
    const fields = matches[1]
      .split(',')
      .map(f => f.trim())
      .filter(f => f && !f.startsWith('(')) // 过滤掉聚合函数
      .map(f => {
        const parts = f.split(/\s+as\s+/i)
        const name = parts.length > 1 ? parts[1].trim() : parts[0].trim()
        return {
          name,
          type: 'STRING',
          comment: ''
        }
      })

    parsedFields.value = fields
  } else {
    parsedFields.value = []
  }
}

// 表单验证
async function validate() {
  if (props.etlType === 'data_integration') {
    // 验证字段映射
    if (!formData.value.fieldMappings || formData.value.fieldMappings.length === 0) {
      throw new Error('请配置字段映射关系')
    }
  } else if (props.etlType === 'sql_task') {
    // 验证SQL脚本
    if (!formData.value.sqlScript) {
      throw new Error('请输入SQL转换脚本')
    }
  }
  return true
}

function resetFields() {
  // Reset logic
}

defineExpose({
  validate,
  resetFields
})
</script>

<style scoped lang="scss">
.transform-step {
  padding: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.mapping-preview {
  .preview-panel {
    border: 1px solid #ebeef5;
    border-radius: 4px;
    overflow: hidden;

    .panel-header {
      padding: 12px 16px;
      background: #f5f7fa;
      border-bottom: 1px solid #ebeef5;
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
    }

    .panel-content {
      padding: 16px;
      min-height: 150px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-content: flex-start;

      .el-tag {
        margin: 0;
      }
    }
  }
}

.sql-editor-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.parsed-info {
  margin-left: 12px;
  color: #67C23A;
  font-size: 13px;
}

.template-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .template-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .template-name {
      font-weight: 600;
      font-size: 15px;
    }
  }

  .template-desc {
    color: #606266;
    margin-bottom: 12px;
    font-size: 13px;
  }

  .template-code {
    background: #f5f7fa;
    padding: 12px;
    border-radius: 4px;
    font-size: 12px;
    overflow-x: auto;
  }
}
</style>
