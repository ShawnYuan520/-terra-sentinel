<template>
  <div class="exploded-gallery">
    <div class="gallery-main">
      <img :src="images[activeIndex]" :alt="`爆炸视图 ${activeIndex + 1}`" class="gallery-img" />
      <div class="gallery-nav">
        <button class="nav-btn" @click="prev" :disabled="images.length <= 1">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <span class="nav-counter">{{ activeIndex + 1 }} / {{ images.length }}</span>
        <button class="nav-btn" @click="next" :disabled="images.length <= 1">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
        </button>
      </div>
    </div>
    <div class="gallery-thumbs">
      <button
        v-for="(img, i) in images"
        :key="i"
        :class="['thumb', { active: i === activeIndex }]"
        @click="activeIndex = i"
      >
        <img :src="img" :alt="`缩略图 ${i + 1}`" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  images: { type: Array, required: true },
})

const activeIndex = ref(0)

function prev() {
  activeIndex.value = (activeIndex.value - 1 + props.images.length) % props.images.length
}
function next() {
  activeIndex.value = (activeIndex.value + 1) % props.images.length
}
</script>

<style scoped>
.exploded-gallery {
  display: flex; flex-direction: column; gap: 12px;
  width: 100%;
}

.gallery-main {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-50);
  border: 1px solid var(--surface-200);
  aspect-ratio: 4/3;
}

.gallery-img {
  width: 100%; height: 100%;
  object-fit: contain;
  transition: opacity var(--duration-fast);
}

.gallery-nav {
  position: absolute; bottom: 12px; left: 50%;
  transform: translateX(-50%);
  display: flex; align-items: center; gap: 10px;
  padding: 6px 12px;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-full);
}

.nav-btn {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  background: none; border: none; color: rgba(255,255,255,0.85);
  cursor: pointer; border-radius: 50%;
  transition: background var(--duration-fast);
}
.nav-btn:hover { background: rgba(255,255,255,0.15); }
.nav-btn:disabled { opacity: 0.3; cursor: default; }

.nav-counter {
  font-size: 12px; color: rgba(255,255,255,0.8);
  min-width: 40px; text-align: center;
}

.gallery-thumbs {
  display: flex; gap: 8px; justify-content: center;
}

.thumb {
  width: 56px; height: 56px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  opacity: 0.6;
  transition: all var(--duration-fast);
  padding: 0; background: none;
}
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.thumb.active { border-color: var(--color-primary); opacity: 1; }
.thumb:hover { opacity: 1; }
</style>
