<template>
  <div class="layer-toggle">
    <div class="section-title">图层控制</div>

    <div class="layer-group" v-for="group in groups" :key="group.name">
      <div class="layer-group-title">{{ group.name }}</div>
      <label
        v-for="layer in group.layers"
        :key="layer.key"
        :class="['layer-item', { active: activeLayers.includes(layer.key) }]"
      >
        <input
          type="checkbox"
          :checked="activeLayers.includes(layer.key)"
          @change="$emit('toggle', layer.key)"
        />
        <span class="layer-dot" :style="{ background: layer.color || '#22C55E' }"></span>
        <span class="layer-name">{{ layer.label }}</span>
      </label>
    </div>

    <div class="layer-group">
      <div class="layer-group-title">底图</div>
      <label
        v-for="bm in basemaps"
        :key="bm.key"
        :class="['layer-item', { active: activeBasemap === bm.key }]"
      >
        <input type="radio" :value="bm.key" :checked="activeBasemap === bm.key" @change="$emit('basemap', bm.key)" />
        <span class="layer-name">{{ bm.label }}</span>
      </label>
    </div>
  </div>
</template>

<script setup>
defineProps({
  activeLayers: { type: Array, default: () => [] },
  activeBasemap: { type: String, default: 'satellite' },
})
defineEmits(['toggle', 'basemap'])

const groups = [
  {
    name: '地形',
    layers: [
      { key: 'dem', label: '高程 DEM', color: '#8B5E3C' },
      { key: 'slope', label: '坡度 Slope', color: '#D97706' },
      { key: 'aspect', label: '坡向 Aspect', color: '#3B82F6' },
    ],
  },
  {
    name: '土壤',
    layers: [
      { key: 'soc', label: '有机碳 SOC', color: '#22C55E' },
      { key: 'ph', label: '土壤 pH', color: '#DC2626' },
      { key: 'sand', label: '砂粒 Sand', color: '#D97706' },
      { key: 'silt', label: '粉粒 Silt', color: '#8B5E3C' },
      { key: 'clay', label: '粘粒 Clay', color: '#3B82F6' },
      { key: 'texture', label: '土壤质地', color: '#A67B5B' },
    ],
  },
  {
    name: '遥感',
    layers: [
      { key: 'landuse', label: '土地覆盖 CLCD', color: '#22C55E' },
      { key: 'ndvi', label: 'NDVI 植被指数', color: '#22C55E' },
    ],
  },
]

const basemaps = [
  { key: 'satellite', label: '卫星影像' },
  { key: 'dark', label: '暗色地图' },
]
</script>

<style scoped>
.layer-toggle { padding: var(--space-3); color: var(--gis-text); user-select: none; }
.layer-group { margin-bottom: var(--space-4); }
.layer-group-title {
  font-size: 11px; font-weight: var(--weight-semibold);
  color: var(--gis-text-dim);
  text-transform: uppercase; letter-spacing: var(--tracking-wider);
  margin-bottom: var(--space-1); padding: var(--space-1) 0;
}
.layer-item {
  display: flex; align-items: center; gap: var(--space-2);
  padding: 5px var(--space-3); border-radius: var(--radius-xs);
  cursor: pointer; font-size: var(--text-sm); color: var(--gis-text-muted);
  transition: all var(--duration-fast) var(--ease-out);
}
.layer-item:hover { background: var(--gis-surface-hover); color: var(--gis-text); }
.layer-item.active { color: var(--gis-text); background: rgba(255,255,255,0.02); }
.layer-item input { display: none; }
.layer-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  box-shadow: 0 0 4px rgba(255,255,255,0.15);
}
.layer-item.active .layer-dot {
  box-shadow: 0 0 6px currentColor;
}
.layer-name { flex: 1; }
</style>
