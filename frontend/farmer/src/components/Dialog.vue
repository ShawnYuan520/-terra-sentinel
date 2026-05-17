<template>
  <Teleport to="body">
    <div class="dialog-overlay" v-if="visible" @click.self="$emit('close')">
      <div class="dialog-box" :style="{ maxWidth: width }">
        <div class="dialog-header">
          <span class="dialog-title">{{ title }}</span>
          <button class="dialog-close" @click="$emit('close')">✕</button>
        </div>
        <div class="dialog-body">
          <slot />
        </div>
        <div class="dialog-footer" v-if="$slots.footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  visible: Boolean,
  title: String,
  width: { type: String, default: '400px' },
})
defineEmits(['close'])
</script>

<style scoped>
.dialog-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex; align-items: center; justify-content: center;
  z-index: 2000;
  animation: fadeIn var(--duration-normal) var(--ease-out) both;
}
.dialog-box {
  background: var(--gis-surface);
  border: 1px solid var(--gis-border-light);
  border-radius: var(--radius-lg);
  width: 90%;
  box-shadow: var(--shadow-xl);
  animation: scaleIn var(--duration-normal) var(--ease-spring) both;
}
.dialog-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--space-5) var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--gis-border);
}
.dialog-title {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--gis-text);
}
.dialog-close {
  background: none; border: none;
  color: var(--gis-text-muted); cursor: pointer;
  font-size: 18px; width: 32px; height: 32px; border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  transition: all var(--duration-fast) var(--ease-out);
}
.dialog-close:hover { color: var(--gis-text); background: var(--gis-surface-hover); }
.dialog-body { padding: var(--space-5); }
.dialog-footer {
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--gis-border);
  display: flex; justify-content: flex-end; gap: var(--space-2);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.92); }
  to { opacity: 1; transform: scale(1); }
}
</style>
