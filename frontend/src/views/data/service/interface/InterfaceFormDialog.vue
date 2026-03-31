<!-- eslint-disable vue/no-v-model-argument -->
<template>
  <el-dialog :title="title" v-model="dialogVisible" width="900px" append-to-body>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="140px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="接口名称" prop="interfaceName">
            <el-input v-model="form.interfaceName" placeholder="请输入接口名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="接口编码" prop="interfaceCode">
            <el-input v-model="form.interfaceCode" placeholder="请输入接口编码" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="数据库类型" prop="interfaceDbType">
            <el-select v-model="form.interfaceDbType" placeholder="请选择数据库类型">
              <el-option v-for="item in dbTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="数据库名称" prop="interfaceDbName">
            <el-input v-model="form.interfaceDbName" placeholder="请输入数据库名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="数据源" prop="interfaceDatasource">
            <el-select v-model="form.interfaceDatasource" filterable placeholder="请选择数据源">
              <el-option v-for="ds in datasourceOptions" :key="ds.dataSourceId" :label="ds.dataSourceName" :value="ds.dataSourceId" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否分页" prop="isPaging">
            <el-radio-group v-model="form.isPaging">
              <el-radio v-for="dict in YES_NO_OPTIONS" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否日期查询" prop="isDateOption">
            <el-radio-group v-model="form.isDateOption">
              <el-radio v-for="dict in YES_NO_OPTIONS" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否合计" prop="isTotal">
            <el-radio-group v-model="form.isTotal">
              <el-radio v-for="dict in YES_NO_OPTIONS" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否二级表头" prop="isSecondTable">
            <el-radio-group v-model="form.isSecondTable">
              <el-radio v-for="dict in YES_NO_OPTIONS" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="登录校验" prop="isLoginVisit">
            <el-radio-group v-model="form.isLoginVisit">
              <el-radio v-for="dict in YES_NO_OPTIONS" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="报警类型" prop="alarmType">
            <el-select v-model="form.alarmType" placeholder="请选择报警类型">
              <el-option v-for="dict in ALARM_TYPE_OPTIONS" :key="dict.value" :label="dict.label" :value="dict.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="接口状态" prop="enable">
            <el-select v-model="form.enable" placeholder="请选择接口状态">
              <el-option v-for="dict in ENABLE_OPTIONS" :key="dict.value" :label="dict.label" :value="dict.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="接口描述" prop="interfaceDesc">
            <el-input v-model="form.interfaceDesc" type="textarea" :rows="2" placeholder="请输入接口描述" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="接口SQL" prop="interfaceSql">
            <el-input v-model="form.interfaceSql" type="textarea" :rows="5" placeholder="请输入接口 SQL（支持模板渲染）" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="合计SQL" prop="totalSql">
            <el-input v-model="form.totalSql" type="textarea" :rows="3" placeholder="可选：合计 SQL" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="业务平台" prop="platformName">
            <el-input v-model="form.platformName" placeholder="请输入业务平台" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="模块名称" prop="moduleName">
            <el-input v-model="form.moduleName" placeholder="请输入模块名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="报表编码" prop="reportCode">
            <el-input v-model="form.reportCode" placeholder="请输入报表编码" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="报表名称" prop="reportName">
            <el-input v-model="form.reportName" placeholder="请输入报表名称" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="handleSubmit">确 定</el-button>
        <el-button @click="handleCancel">取 消</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { YES_NO_OPTIONS, ALARM_TYPE_OPTIONS, ENABLE_OPTIONS, DB_TYPE_OPTIONS } from './constants'

const props = defineProps({
  modelValue: Boolean,
  title: String,
  form: { type: Object, required: true },
  rules: Object,
  datasourceOptions: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'submit', 'cancel'])

const formRef = ref(null)
const dbTypeOptions = DB_TYPE_OPTIONS

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

function handleCancel() {
  emit('cancel')
  emit('update:modelValue', false)
}

function handleSubmit() {
  formRef.value.validate(valid => {
    if (!valid) return
    emit('submit')
  })
}
</script>
