<template>
<div>
    <el-row :gutter="24">
        <el-col :span="12">
        <el-card>
            <template #header>
            <span>来源</span>
            </template>
            <db-source-selector 
            v-model:source="detail.source" 
            v-model:columns="sourceColumns"
            :datasourceMultiple="true"
            :databaseMultiple="true"
            />
        </el-card>
        </el-col>
        <el-col :span="12">
        <el-card>
            <template #header>
            <span>目标</span>
            </template>
            <db-source-selector 
            v-model:source="detail.target" 
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
        <field-mapping v-model:source-columns="sourceColumns"
            v-model:target-columns="targetColumns" 
            v-model:mappings="fieldMappings"
            v-model:defaultMapping="defaultMapping" />
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
import { reactive, ref, toRef, watch } from 'vue'
import FieldMapping from '@/components/FieldMapping'
import DbSourceSelector from './DbSourceSelector.vue';


const props = defineProps({
  detail: {
    type: Object,
        default: () => ({
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

// const detail = reactive(props.detail)
const detail = toRef(props.detail)
const sourceColumns = ref([])
const targetColumns = ref([])
const fieldMappings = ref([])
const defaultMapping = ref(false)
const syncConfig = ref({
    where: '',
    mode: {
        type: 'full',
        incrementField: '',
        incrementType: ''
    }
})

watch(() => JSON.stringify(props.detail), (v) => {
    detail.value = JSON.parse(v)
    emit('update:detail', detail.value)
})

// watch(() => detail.value.source, (val) => { 
//     const datasourceIds = val.dataSourceIds
//     console.log('watch datasourceIds', datasourceIds)
// })
const showDetails = () => {
    console.log(detail.value, props.detail)
}

</script>

<style scoped>
</style>