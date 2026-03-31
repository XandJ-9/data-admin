<template>
  <el-dialog :title="execTitle" v-model="dialogVisible" width="900px" append-to-body>
    <el-form label-width="120px">
      <el-row :gutter="20">
        <el-col :span="24">
          <el-form-item label="参数(JSON)">
            <el-input
              v-model="execForm.paramsJson"
              type="textarea"
              :rows="5"
              placeholder='例如: {&#10;  "startDate": "2024-01-01",&#10;  "endDate": "2024-12-31"&#10;}'
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="每页条数">
            <el-input-number v-model="execForm.pageSize" :min="1" :max="5000" controls-position="right" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="偏移量">
            <el-input-number v-model="execForm.offset" :min="0" controls-position="right" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
    <el-divider />
    <el-table v-loading="execLoading" :data="execRows" height="300px" style="width: 100%">
      <el-table-column
        v-for="col in execColumns"
        :key="col"
        :prop="col"
        :label="col"
        :show-overflow-tooltip="true"
      />
    </el-table>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="handleExecute">执行查询</el-button>
        <el-button type="warning" @click="handleExport">导出数据</el-button>
        <el-button @click="emit('update:modelValue', false)">关 闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { executeInterfaceById } from '@/api/data/service'

const { proxy } = getCurrentInstance()

const props = defineProps({
  modelValue: Boolean,
  execTitle: { type: String, default: '执行查询' },
  interfaceId: { type: [Number, String], default: null }
})

const emit = defineEmits(['update:modelValue'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const execLoading = ref(false)
const execRows = ref([])
const execColumns = ref([])
const execForm = ref({ paramsJson: undefined, pageSize: 50, offset: 0 })

watch(() => props.modelValue, (val) => {
  if (!val) {
    execRows.value = []
    execColumns.value = []
  }
})

function handleExecute() {
  const id = props.interfaceId
  if (!id) return

  let paramsObj = null
  if (execForm.value.paramsJson?.trim()) {
    try {
      paramsObj = JSON.parse(execForm.value.paramsJson)
    } catch {
      proxy.$modal.msgError('参数JSON格式错误')
      return
    }
  }

  execLoading.value = true
  executeInterfaceById(id, {
    params: paramsObj || {},
    pageSize: execForm.value.pageSize,
    offset: execForm.value.offset
  }).then(res => {
    const rows = res.data?.rows
    execColumns.value = res.data?.columns || []
    execRows.value = rows.map(item => {
      const rowObj = {}
      execColumns.value.forEach((col, index) => { rowObj[col] = item[index] })
      return rowObj
    })
  }).catch(err => {
    proxy.$modal.msgError(err?.msg || '执行失败')
  }).finally(() => {
    execLoading.value = false
  })
}

function handleExport() {
  const id = props.interfaceId
  if (!id) return
  proxy.download(
    `/dataservice/interface-info/${id}/export-data`,
    {},
    `interface_${id}_data.xlsx`
  )
}
</script>
