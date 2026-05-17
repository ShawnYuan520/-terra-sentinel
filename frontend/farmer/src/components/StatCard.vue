<template>
  <div class="stat-card" :style="{ '--accent': accent }">
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value">
      <span class="stat-num">{{ value }}</span>
      <span class="stat-unit" v-if="unit">{{ unit }}</span>
    </div>
    <div class="stat-trend" v-if="trend">
      <span :class="['trend-arrow', trend > 0 ? 'up' : 'down']">
        {{ trend > 0 ? '▲' : '▼' }}
      </span>
      <span class="trend-value" v-if="trendValue">{{ trendValue }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  unit: String,
  accent: { type: String, default: '#2EC85D' },
  trend: Number,
  trendValue: String,
})
</script>

<style scoped>
.stat-card {
  background: var(--gis-surface);
  border: 1px solid var(--gis-border);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition:
    transform var(--duration-normal) var(--ease-out),
    box-shadow var(--duration-normal) var(--ease-out),
    border-color var(--duration-normal) var(--ease-out);
}
.stat-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-card-hover);
  border-color: var(--gis-border-light);
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  background: var(--accent, var(--color-primary));
  transform-origin: left;
  transform: scaleX(0.4);
  transition: transform var(--duration-slow) var(--ease-out);
}
.stat-card:hover::before { transform: scaleX(1); }
.stat-label {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--gis-text-muted);
}
.stat-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.stat-num {
  font-size: var(--text-4xl);
  font-weight: var(--weight-bold);
  color: var(--gis-text);
  font-family: var(--font-mono);
  line-height: 1.15;
  letter-spacing: var(--tracking-tight);
}
.stat-unit {
  font-size: var(--text-sm);
  color: var(--gis-text-muted);
}
.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
}
.trend-arrow.up { color: #4ADE80; }
.trend-arrow.down { color: #F87171; }
.trend-value { color: var(--gis-text-muted); }
</style>
