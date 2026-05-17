<template>
  <div class="product-card">
    <div class="product-accent" :style="{ background: accent }"></div>
    <ProductImage v-if="imageType" :type="imageType" :photo="photo" />
    <div class="product-body">
      <div class="product-header">
        <h3 class="product-name">{{ product.name }}</h3>
        <span class="badge badge-info">{{ product.type }}</span>
      </div>
      <p class="product-desc text-sm text-muted">{{ product.description }}</p>
      <div class="product-specs">
        <div class="spec-item" v-if="product.suitable_crops">
          <span class="spec-label">适用作物</span>
          <span class="spec-value">{{ product.suitable_crops }}</span>
        </div>
        <div class="spec-item" v-if="product.suitable_soil">
          <span class="spec-label">适用土壤</span>
          <span class="spec-value">{{ product.suitable_soil }}</span>
        </div>
        <div class="spec-item" v-if="product.usage_guide">
          <span class="spec-label">用量</span>
          <span class="spec-value">{{ product.usage_guide }}</span>
        </div>
        <div class="spec-item" v-if="product.decomposition_days">
          <span class="spec-label">腐解周期</span>
          <span class="spec-value">{{ product.decomposition_days }} 天</span>
        </div>
      </div>
      <div class="product-features" v-if="product.features?.length">
        <span v-for="f in product.features" :key="f" class="tag">{{ f }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import ProductImage from './ProductImage.vue'
defineProps({
  product: { type: Object, required: true },
  accent: { type: String, default: '#2EC85D' },
  imageType: { type: String, default: '' },
  photo: { type: String, default: '' },
})
</script>

<style scoped>
.product-card {
  background: var(--surface-0);
  border: 1px solid var(--surface-200);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  box-shadow: var(--shadow-xs);
  transition: all var(--duration-normal) var(--ease-out);
}
.product-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--surface-300);
  transform: translateY(-2px);
}
.product-accent {
  width: 4px; flex-shrink: 0;
}
.product-body {
  flex: 1; padding: var(--space-5);
  display: flex; flex-direction: column; gap: var(--space-3);
}
.product-header {
  display: flex; justify-content: space-between; align-items: flex-start;
}
.product-name {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--surface-900);
}
.product-desc {
  line-height: var(--leading-relaxed);
  font-size: var(--text-sm);
  color: var(--surface-700);
}
.product-specs {
  display: flex; flex-direction: column; gap: 6px;
  background: var(--surface-50);
  border-radius: var(--radius-sm);
  padding: 12px;
}
.spec-item {
  display: flex; gap: var(--space-2);
  font-size: var(--text-sm);
}
.spec-label { color: var(--surface-700); min-width: 70px; }
.spec-value { color: var(--surface-900); font-weight: var(--weight-medium); }
.product-features {
  display: flex; flex-wrap: wrap; gap: 6px;
  margin-top: var(--space-1);
}
.tag {
  display: inline-block;
  padding: 3px 10px;
  background: var(--color-primary-50);
  border-radius: var(--radius-xs);
  font-size: 11px;
  color: var(--color-primary-300);
  font-weight: var(--weight-medium);
}
</style>
