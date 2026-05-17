<template>
  <div class="field-selector">
    <div class="section-title">
      我的地块
      <span class="count-badge">{{ fields.length }}</span>
    </div>

    <div class="field-list" v-if="fields.length">
      <div
        v-for="f in fields"
        :key="f.id"
        :class="['field-item', { active: selectedId === f.id }]"
        @click="$emit('select', f)"
      >
        <div class="field-icon">
          <span v-if="f.crop_type === '玉米'"><Crop :size="16" /></span>
          <span v-else-if="f.crop_type === '小麦'"><Wheat :size="16" /></span>
          <span v-else-if="f.crop_type === '大豆'"><Bean :size="16" /></span>
          <span v-else-if="f.crop_type === '水稻'"><CookingPot :size="16" /></span>
          <span v-else><Sprout :size="16" /></span>
        </div>
        <div class="field-info">
          <div class="field-name">{{ f.name }}</div>
          <div class="field-meta">{{ f.crop_type || '未指定' }} · {{ f.area_ha }}ha</div>
        </div>
      </div>
    </div>

    <div class="field-empty" v-else>
      <p>暂无田块数据</p>
    </div>

    <button class="btn btn-primary btn-sm btn-block" @click="$emit('new-field')" style="margin-top: var(--space-md)">
      + 新建田块
    </button>
  </div>
</template>

<script setup>
import { Bean, CookingPot, Crop, Sprout, Wheat } from 'lucide-vue-next'
defineProps({
  fields: { type: Array, default: () => [] },
  selectedId: String,
})
defineEmits(['select', 'new-field'])
</script>

<style scoped>
.field-selector { padding: var(--space-3); }
.count-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 20px; height: 20px;
  font-size: 11px; font-weight: var(--weight-semibold);
  background: var(--color-primary); color: #fff;
  border-radius: var(--radius-full);
  padding: 0 6px;
}
.field-list {
  display: flex; flex-direction: column; gap: 2px;
  max-height: 320px; overflow-y: auto;
}
.field-item {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 1px solid transparent;
  transition: all var(--duration-fast) var(--ease-out);
}
.field-item:hover { background: var(--gis-surface-hover); }
.field-item.active {
  background: var(--gis-surface-active);
  border-color: rgba(46, 200, 93, 0.30);
}
.field-icon {
  width: 30px; height: 30px; text-align: center; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-xs);
  background: rgba(255,255,255,0.03);
}
.field-item.active .field-icon { background: rgba(46, 200, 93, 0.10); }
.field-icon :deep(svg) { opacity: 0.55; }
.field-item.active .field-icon :deep(svg) { opacity: 0.85; }
.field-name { font-size: var(--text-sm); font-weight: var(--weight-medium); color: var(--gis-text); }
.field-meta { font-size: var(--text-xs); color: var(--gis-text-dim); margin-top: 2px; }
.field-empty { text-align: center; padding: var(--space-4); color: var(--gis-text-dim); font-size: var(--text-sm); }
</style>
