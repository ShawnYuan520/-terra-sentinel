<template>
  <div class="model-viewer-wrap" :class="{ loading: isLoading }">
    <model-viewer
      :src="src"
      :alt="alt"
      camera-controls
      auto-rotate
      auto-rotate-delay="1000"
      rotation-per-second="25deg"
      interaction-prompt="auto"
      shadow-intensity="0.6"
      shadow-softness="0.8"
      exposure="1.2"
      environment-image="neutral"
      loading="lazy"
      reveal="auto"
      @load="isLoading = false"
      @error="hasError = true"
      style="width: 100%; height: 100%;"
    >
      <div slot="progress-bar" v-if="isLoading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <span>加载 3D 模型中…</span>
      </div>
    </model-viewer>
    <div v-if="hasError" class="error-overlay">
      <span>模型加载失败</span>
    </div>
    <div class="viewer-hint" v-if="!isLoading && !hasError">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 2v10l6.5-6.5"/></svg>
      拖拽旋转 · 滚轮缩放
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import '@google/model-viewer'

defineProps({
  src: { type: String, required: true },
  alt: { type: String, default: '3D 模型' },
})

const isLoading = ref(true)
const hasError = ref(false)
</script>

<style scoped>
.model-viewer-wrap {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 320px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: linear-gradient(135deg, var(--surface-50) 0%, var(--surface-100) 100%);
  border: 1px solid var(--surface-200);
}

model-viewer {
  --poster-color: transparent;
}

.loading-overlay,
.error-overlay {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 12px;
  font-size: var(--text-sm);
  color: var(--surface-500);
  background: var(--surface-50);
  z-index: 2;
}

.loading-spinner {
  width: 32px; height: 32px;
  border: 3px solid var(--surface-200);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.error-overlay { color: var(--color-danger); }

.viewer-hint {
  position: absolute;
  bottom: 12px; left: 50%;
  transform: translateX(-50%);
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-full);
  font-size: 11px; color: rgba(255,255,255,0.8);
  pointer-events: none;
  z-index: 1;
}
</style>
