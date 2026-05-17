<template>
  <div class="draw-bar">
    <span class="draw-info">
      <span class="draw-dot"></span>
      绘制模式 · {{ vertexCount }} 个顶点
    </span>
    <div class="draw-actions">
      <button class="btn btn-primary btn-sm" @click="$emit('finish')" :disabled="vertexCount < 3">完成绘制</button>
      <button class="btn btn-ghost btn-sm" @click="$emit('cancel')">取消</button>
    </div>
  </div>
</template>

<script setup>
defineProps({ vertexCount: { type: Number, default: 0 } })
defineEmits(['finish', 'cancel'])
</script>

<style scoped>
.draw-bar {
  position: absolute; top: 12px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: var(--space-lg);
  background: var(--gis-surface);
  border: 1px solid var(--gis-border);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-lg);
  z-index: 1000;
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(8px);
}
.draw-dot {
  display: inline-block; width: 6px; height: 6px;
  border-radius: 50%; background: #22C55E;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.draw-info {
  font-size: var(--text-sm); color: var(--gis-text-muted);
  display: flex; align-items: center; gap: var(--space-sm);
}
.draw-actions { display: flex; gap: var(--space-sm); }
</style>
