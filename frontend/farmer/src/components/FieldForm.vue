<template>
  <div class="field-form">
    <div class="form-group">
      <label>田块名称</label>
      <input class="form-input" v-model="local.name" placeholder="输入田块名称" />
    </div>
    <div class="form-group">
      <label>作物类型</label>
      <select class="form-input" v-model="local.crop_type">
        <option v-for="c in crops" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>
    <div class="form-group">
      <label>面积</label>
      <div class="area-row">
        <input class="form-input area-input" :value="local.area_ha" disabled />
        <span class="area-unit">公顷</span>
        <input class="form-input area-input" :value="+(local.area_ha * 15).toFixed(2)" disabled />
        <span class="area-unit">亩</span>
      </div>
    </div>
    <div class="form-actions">
      <button class="btn btn-ghost btn-sm" @click="$emit('cancel')">取消</button>
      <button class="btn btn-primary btn-sm" @click="$emit('save', local)" :disabled="!local.name">保存田块</button>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({ modelValue: Object })
defineEmits(['save', 'cancel'])

const local = reactive({ name: '', crop_type: '玉米', area_ha: 0, ...props.modelValue })
watch(() => props.modelValue, v => { if (v) Object.assign(local, v) }, { immediate: true })

const crops = ['玉米', '小麦', '大豆', '水稻', '棉花', '高粱', '马铃薯', '甜菜']
</script>

<style scoped>
.field-form { display: flex; flex-direction: column; gap: var(--space-md); }
.area-row {
  display: flex; align-items: center; gap: var(--space-xs);
}
.area-input {
  flex: 1; text-align: center;
}
.area-unit {
  font-size: var(--text-xs);
  color: var(--gis-text-muted);
  flex-shrink: 0;
}
.form-actions {
  display: flex; justify-content: flex-end; gap: var(--space-sm);
  margin-top: var(--space-sm);
}
</style>
