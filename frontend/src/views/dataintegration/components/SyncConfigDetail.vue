<template>
<div>
    <el-row :gutter="24">
        <el-col :span="12">
        <el-card>
            <template #header>
            <span>来源</span>
            </template>
            <db-source-selector 
            v-model:source="source" 
            v-model:columns="sourceColumns"
            :datasourceMultiple="true"
            :databaseMultiple="true"
            :tableMultiple="false"
            />
        </el-card>
        </el-col>
        <el-col :span="12">
        <el-card>
            <template #header>
            <span>目标</span>
            </template>
            <db-source-selector 
            v-model:source="target" 
            v-model:columns="targetColumns" />
        </el-card>
        </el-col>
    </el-row>

    <el-row>
        <el-col :span="24"> 
        <el-card style="margin-top: 16px">
        <template #header>
            <span>字段映射</span>
        </template>
        <Field-mapping v-model:source-columns="sourceColumns"
            v-model:target-columns="targetColumns" 
            v-model:mappings="fieldMappings"/>
        </el-card>
        </el-col>
    </el-row>

    <el-row>
        <el-col :span="24"> 
        <el-card style="margin-top: 16px">
            <template #header>
                <span>同步条件</span>
            </template>
            <el-form :model="syncConfig" label-width="120px">
                <el-form-item label="where条件">
                    <el-input v-model="syncConfig.where" type="textarea" :rows="2" placeholder="示例：status = 1" />
                </el-form-item>
                <el-form-item label="同步方式">
                    <el-radio-group v-model="syncConfig.mode.type">
                        <el-radio label="full">全量</el-radio>
                        <el-radio label="incremental">增量</el-radio>
                    </el-radio-group>
                </el-form-item>
                <el-form-item v-if="syncConfig.mode.type === 'incremental'" label="增量字段">
                    <el-select v-model="syncConfig.mode.incrementField" filterable allow-create placeholder="选择或输入增量字段"
                        style="width: 240px">
                        <el-option v-for="c in sourceColumns" :key="c" :label="c" :value="c" />
                    </el-select>
                    <el-select v-model="syncConfig.mode.incrementType" style="width: 180px; margin-left: 12px">
                        <el-option label="自增ID" value="id" />
                        <el-option label="时间戳" value="timestamp" />
                        <el-option label="自定义" value="custom" />
                    </el-select>
                </el-form-item>
            </el-form>
        </el-card> 
        </el-col>
    </el-row>

    
</div>
</template>

<script setup>
import { onMounted, reactive, ref, toRef, toRefs, watch } from 'vue'
import FieldMapping from '@/components/FieldMapping'
import DbSourceSelector from './DbSourceSelector.vue';


const props = defineProps({
  detail: {
    type: Object,
    default: () => ({
            source: {},
            target: {},
            where: '',
            mode: {
                type: 'full',
                incrementalField: '',
                incrementType: ''
            }
        })
  }
})

const emit = defineEmits(['update:detail'])


const detail = ref({})
const source = ref({})
const target = ref({})
const sourceColumns = ref([])
const targetColumns = ref([])
const fieldMappings = ref([])
const syncConfig = ref({
    where: '',
    mode: {
        type: 'full',
        incrementField: '',
        incrementType: ''
    }
})


watch(() => JSON.stringify(props.detail || {}), v => {
    // source.value = props.detail.source || {}
    detail.value = props.detail || {}
    // console.log('watch config.detail', detail.value)
    source.value = detail.value.source || {}
    target.value = detail.value.target || {}
    sourceColumns.value = detail.value.sourceColumns || []
    targetColumns.value = detail.value.targetColumns || []
    fieldMappings.value = detail.value.fieldMappings || []
    syncConfig.value = detail.value.syncConfig || {
        where: '',
        mode: {
            type: 'full',
            incrementField: '',
            incrementType: ''
        }
    }
})

// watch(() => JSON.stringify(props.detail.target || {}), v => {
//     target.value = props.detail.target || {}
//     console.log('watch config.detail.target', target.value)
// })

watch(() => JSON.stringify(source.value), (v) => {
    // console.log('watch source', JSON.parse(v))
    detail.value.source = JSON.parse(v)
    emit('update:detail', detail.value)
})

watch(() => JSON.stringify(target.value), (v) => {
    // console.log('watch target', JSON.parse(v))
    detail.value.target = JSON.parse(v)
    emit('update:detail', detail.value)
})

watch(() => JSON.stringify(sourceColumns.value), (v) => {
    // console.log('watch sourceColumns', JSON.parse(v))
    detail.value.sourceColumns = JSON.parse(v)
    emit('update:detail', detail.value)
})

watch(() => JSON.stringify(targetColumns.value), (v) => {
    // console.log('watch targetColumns', JSON.parse(v))
    detail.value.targetColumns = JSON.parse(v)
    emit('update:detail', detail.value)
})

watch(() => JSON.stringify(fieldMappings.value), (v) => {
    // console.log('watch fieldMappings', JSON.parse(v))
    detail.value.fieldMappings = JSON.parse(v)
    emit('update:detail', detail.value)
})

watch(() => JSON.stringify(syncConfig.value), (v) => {
    // console.log('watch syncConfig', JSON.parse(v))
    detail.value.syncConfig = JSON.parse(v)
    emit('update:detail', detail.value)
})

onMounted(() => {
    // console.log('syncConfigDetail onMounted', detail.value)
})

</script>

<style scoped>
</style>