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
            v-model:columns="detail.sourceColumns"
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
            v-model:source="detail.target" 
            v-model:columns="detail.targetColumns" />
        </el-card>
        </el-col>
    </el-row>

    <el-row>
        <el-col :span="24"> 
        <el-card style="margin-top: 16px">
        <template #header>
            <span>字段映射</span>
        </template>
        <Field-mapping v-model:source-columns="detail.sourceColumns"
            v-model:target-columns="detail.targetColumns" 
            v-model:mappings="detail.fieldMappings"/>
        </el-card>
        </el-col>
    </el-row>

    <el-row>
        <el-col :span="24"> 
        <el-card style="margin-top: 16px">
            <template #header>
                <span>同步条件</span>
            </template>
            <el-form :model="detail.syncConfig" label-width="120px">
                <el-form-item label="where条件">
                    <el-input v-model="detail.syncConfig.where" type="textarea" :rows="2" placeholder="示例：status = 1" />
                </el-form-item>
                <el-form-item label="同步方式">
                    <el-radio-group v-model="detail.syncConfig.mode.type">
                        <el-radio label="full">全量</el-radio>
                        <el-radio label="incremental">增量</el-radio>
                    </el-radio-group>
                </el-form-item>
                <el-form-item v-if="detail.syncConfig.mode.type === 'incremental'" label="增量字段">
                    <el-select v-model="detail.syncConfig.mode.incrementField" filterable allow-create placeholder="选择或输入增量字段"
                        style="width: 240px">
                        <el-option v-for="c in detail.sourceColumns" :key="c" :label="c" :value="c" />
                    </el-select>
                    <el-select v-model="detail.syncConfig.mode.incrementType" style="width: 180px; margin-left: 12px">
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
import { watch } from 'vue'
import { useVModel } from '@vueuse/core'
import FieldMapping from '@/components/FieldMapping'
import DbSourceSelector from './DbSourceSelector.vue';

const props = defineProps({
  detail: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:detail'])

const detail = useVModel(props, 'detail', emit, { deep: true })

const ensureDefaults = () => {
    // If detail is null/undefined, make it an object
    if (!detail.value) {
        detail.value = {}
    }
    
    const d = detail.value
    let changed = false
    
    if (!d.source) { d.source = {}; changed = true }
    if (!d.target) { d.target = {}; changed = true }
    if (!d.sourceColumns) { d.sourceColumns = []; changed = true }
    if (!d.targetColumns) { d.targetColumns = []; changed = true }
    if (!d.fieldMappings) { d.fieldMappings = []; changed = true }
    if (!d.syncConfig) { 
        d.syncConfig = { 
            where: '', 
            mode: { type: 'full', incrementField: '', incrementType: '' } 
        }
        changed = true 
    } else {
        if (!d.syncConfig.mode) {
             d.syncConfig.mode = { type: 'full', incrementField: '', incrementType: '' }
             changed = true
        }
    }
    
    // Trigger update if we modified structure
    // Note: Mutating d in place (which is detail.value) might trigger deep watch
    // but explicit assignment ensures emit works if useVModel relies on it.
    if (changed) {
        detail.value = { ...d } // spread to create new reference to ensure update triggers
    }
}

watch(() => detail.value, ensureDefaults, { immediate: true, deep: true })

</script>

<style scoped>
</style>