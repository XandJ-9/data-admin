<template>
  <el-form :model="modelValue" :label-position="labelPosition" :inline="inline" class="select-form">
    <el-form-item
      v-for="(field, index) in fields"
      :key="field.prop"
      :label="field.label"
      :prop="field.prop"
      :rules="field.rules"
      :style="field.style"
    >
      <el-select
        v-model="modelValue[field.prop]"
        :placeholder="field.placeholder || '请选择' + field.label"
        :disabled="field.disabled"
        :loading="field.loading"
        :multiple="field.multiple"
        :value-key="field.valueKey || 'value'"
        filterable
        clearable
        @change="(val) => handleChange(val, field, index)"
      >
        <el-option
          v-for="opt in field.options"
          :key="opt[field.optionValue || 'value']"
          :label="opt[field.optionLabel || 'label']"
          :value="opt[field.optionValue || 'value']"
        />
      </el-select>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  // 表单数据绑定对象
  modelValue: {
    type: Object,
    required: true,
    default: () => ({})
  },
  // 字段配置列表
  // Array<{
  //   prop: string, // 字段名
  //   label: string, // 标签
  //   options: Array<{ label: string, value: any }>, // 选项列表
  //   placeholder?: string,
  //   disabled?: boolean,
  //   loading?: boolean, // 选项加载中
  //   multiple?: boolean, // 是否多选
  //   valueKey?: string, // 对象类型值的唯一键
  //   optionLabel?: string, // 选项标签字段名，默认 'label'
  //   optionValue?: string, // 选项值字段名，默认 'value'
  //   rules?: Array // 校验规则
  // }>
  fields: {
    type: Array,
    default: () => []
  },
  labelWidth: {
    type: String,
    default: '5px'
  },
  labelPosition: {
    type: String,
    default: 'left'
  },
  inline: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

/**
 * 处理下拉框值变化
 * @param val 当前选中的值
 * @param field 当前字段配置
 * @param index 当前字段在 fields 中的索引
 */
const handleChange = (val, field, index) => {
  // 触发 update:modelValue 事件，保持双向绑定
  emit('update:modelValue', props.modelValue)
  
  // 触发 change 事件，传递当前变更的字段信息
  // 父组件可以根据 prop 或 index 来判断是哪个选择框发生了变化，从而更新后续的选择框选项
  emit('change', {
    prop: field.prop,
    value: val,
    index: index,
    field: field
  })
}
</script>

<style scoped>
.select-form .el-select {
  width: 100%;
}
</style>
