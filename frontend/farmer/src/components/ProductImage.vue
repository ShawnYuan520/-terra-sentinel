<template>
  <div class="prod-img" :class="'img-' + type">
    <img v-if="photo" :src="photo" :alt="type" class="prod-photo" />
    <!-- 腐解剂-速效 -->
    <svg v-else-if="type === 'decomposer-fast'" viewBox="0 0 120 100" fill="none">
      <rect width="120" height="100" rx="4" fill="#0C1117"/>
      <circle cx="60" cy="38" r="22" fill="none" stroke="#22C55E" stroke-width="1.5"/>
      <circle cx="60" cy="38" r="12" fill="#22C55E" opacity="0.6"/>
      <path d="M44 38h32M60 22v32" stroke="#4ADE80" stroke-width="1.5" stroke-linecap="round"/>
      <rect x="20" y="72" width="32" height="16" rx="3" fill="#131C26" stroke="#22C55E" stroke-width="1"/>
      <rect x="68" y="72" width="32" height="16" rx="3" fill="#131C26" stroke="#22C55E" stroke-width="1"/>
      <circle cx="36" cy="80" r="4" fill="#4ADE80" opacity="0.5"/>
      <circle cx="84" cy="80" r="4" fill="#4ADE80" opacity="0.5"/>
      <text x="60" y="97" text-anchor="middle" fill="#4ADE80" font-size="8" font-family="Inter,sans-serif">速效腐解</text>
    </svg>

    <!-- 腐解剂-标准 -->
    <svg v-else-if="type === 'decomposer-standard'" viewBox="0 0 120 100" fill="none">
      <rect width="120" height="100" rx="4" fill="#1F1410"/>
      <circle cx="60" cy="42" r="24" fill="none" stroke="#8B5E3C" stroke-width="1.5"/>
      <ellipse cx="60" cy="42" rx="14" ry="8" fill="#8B5E3C" opacity="0.4"/>
      <path d="M36 46 Q48 28 60 46 Q72 64 84 46" stroke="#A67B5B" stroke-width="1.5" fill="none"/>
      <rect x="30" y="72" width="60" height="14" rx="3" fill="#2D1F15" stroke="#8B5E3C" stroke-width="1"/>
      <circle cx="42" cy="79" r="2.5" fill="#A67B5B" opacity="0.6"/>
      <circle cx="54" cy="79" r="2.5" fill="#A67B5B" opacity="0.6"/>
      <circle cx="66" cy="79" r="2.5" fill="#A67B5B" opacity="0.6"/>
      <circle cx="78" cy="79" r="2.5" fill="#A67B5B" opacity="0.6"/>
      <text x="60" y="97" text-anchor="middle" fill="#A67B5B" font-size="8" font-family="Inter,sans-serif">温和腐解</text>
    </svg>

    <!-- 拖拉机 -->
    <svg v-else-if="type === 'tractor'" viewBox="0 0 120 100" fill="none">
      <rect width="120" height="100" rx="4" fill="#0C1117"/>
      <!-- 车身 -->
      <rect x="16" y="40" width="52" height="24" rx="4" fill="#131C26" stroke="#22C55E" stroke-width="1.2"/>
      <!-- 驾驶室 -->
      <rect x="40" y="20" width="28" height="20" rx="3" fill="#0C1117" stroke="#22C55E" stroke-width="1.2"/>
      <rect x="44" y="24" width="20" height="12" rx="2" fill="#3B82F6" opacity="0.25"/>
      <!-- 大轮 -->
      <circle cx="32" cy="70" r="12" fill="#111827" stroke="#22C55E" stroke-width="2"/>
      <circle cx="32" cy="70" r="5" fill="#131C26"/>
      <circle cx="32" cy="70" r="2" fill="#4ADE80" opacity="0.5"/>
      <!-- 小轮 -->
      <circle cx="76" cy="74" r="8" fill="#111827" stroke="#22C55E" stroke-width="1.5"/>
      <circle cx="76" cy="74" r="3" fill="#131C26"/>
      <!-- 排气管 -->
      <rect x="20" y="28" width="4" height="14" rx="1" fill="#64748B"/>
      <text x="60" y="97" text-anchor="middle" fill="#4ADE80" font-size="8" font-family="Inter,sans-serif">智能拖拉机</text>
    </svg>

    <!-- 收割机 -->
    <svg v-else-if="type === 'harvester'" viewBox="0 0 120 100" fill="none">
      <rect width="120" height="100" rx="4" fill="#1F1408"/>
      <!-- 割台 -->
      <rect x="8" y="44" width="36" height="8" rx="2" fill="#D97706" opacity="0.5" stroke="#D97706" stroke-width="1"/>
      <!-- 车身 -->
      <rect x="28" y="28" width="48" height="26" rx="4" fill="#2D1A08" stroke="#8B5E3C" stroke-width="1.2"/>
      <!-- 驾驶室 -->
      <rect x="48" y="10" width="24" height="18" rx="3" fill="#1F1408" stroke="#8B5E3C" stroke-width="1"/>
      <rect x="52" y="14" width="16" height="10" rx="2" fill="#3B82F6" opacity="0.2"/>
      <!-- 轮子 -->
      <circle cx="36" cy="62" r="10" fill="#111827" stroke="#8B5E3C" stroke-width="1.5"/>
      <circle cx="72" cy="66" r="8" fill="#111827" stroke="#8B5E3C" stroke-width="1.5"/>
      <!-- 粮仓 -->
      <rect x="70" y="34" width="18" height="12" rx="2" fill="#D97706" opacity="0.2" stroke="#D97706" stroke-width="1"/>
      <text x="60" y="97" text-anchor="middle" fill="#D97706" font-size="8" font-family="Inter,sans-serif">联合收割机</text>
    </svg>

    <!-- 喷雾器 -->
    <svg v-else-if="type === 'sprayer'" viewBox="0 0 120 100" fill="none">
      <rect width="120" height="100" rx="4" fill="#081420"/>
      <!-- 无人机 -->
      <line x1="24" y1="30" x2="94" y2="30" stroke="#3B82F6" stroke-width="1.5" opacity="0.4"/>
      <ellipse cx="60" cy="38" rx="26" ry="8" fill="#1A2940" stroke="#3B82F6" stroke-width="1.2"/>
      <rect x="44" y="28" width="32" height="8" rx="2" fill="#1A2940" stroke="#3B82F6" stroke-width="1"/>
      <!-- 旋翼 -->
      <circle cx="38" cy="38" r="6" fill="none" stroke="#60A5FA" stroke-width="1" opacity="0.5"/>
      <circle cx="82" cy="38" r="6" fill="none" stroke="#60A5FA" stroke-width="1" opacity="0.5"/>
      <!-- 喷杆 -->
      <line x1="8" y1="48" x2="112" y2="48" stroke="#3B82F6" stroke-width="1" opacity="0.3" stroke-dasharray="4 2"/>
      <!-- 喷雾 -->
      <circle cx="30" cy="56" r="2" fill="#60A5FA" opacity="0.4"/>
      <circle cx="50" cy="58" r="2" fill="#60A5FA" opacity="0.4"/>
      <circle cx="70" cy="58" r="2" fill="#60A5FA" opacity="0.4"/>
      <circle cx="90" cy="56" r="2" fill="#60A5FA" opacity="0.4"/>
      <!-- 药箱 -->
      <rect x="52" y="52" width="16" height="10" rx="2" fill="#1A2940" stroke="#3B82F6" stroke-width="1"/>
      <text x="60" y="97" text-anchor="middle" fill="#60A5FA" font-size="8" font-family="Inter,sans-serif">智能喷雾器</text>
    </svg>

    <!-- 旋耕机 -->
    <svg v-else-if="type === 'tiller'" viewBox="0 0 120 100" fill="none">
      <rect width="120" height="100" rx="4" fill="#1F1510"/>
      <!-- 机架 -->
      <rect x="16" y="38" width="88" height="8" rx="2" fill="#3D2A1A" stroke="#8B5E3C" stroke-width="1"/>
      <!-- 刀片 -->
      <line x1="28" y1="46" x2="28" y2="64" stroke="#8B5E3C" stroke-width="2"/>
      <line x1="40" y1="46" x2="40" y2="64" stroke="#8B5E3C" stroke-width="2"/>
      <line x1="52" y1="46" x2="52" y2="64" stroke="#8B5E3C" stroke-width="2"/>
      <line x1="64" y1="46" x2="64" y2="64" stroke="#8B5E3C" stroke-width="2"/>
      <line x1="76" y1="46" x2="76" y2="64" stroke="#8B5E3C" stroke-width="2"/>
      <line x1="88" y1="46" x2="88" y2="64" stroke="#8B5E3C" stroke-width="2"/>
      <!-- 土壤 -->
      <path d="M10 68 Q30 62 50 68 Q70 74 90 68 Q110 62 120 68" stroke="#A67B5B" stroke-width="1" fill="none" opacity="0.4"/>
      <path d="M10 74 Q30 68 50 74 Q70 80 90 74 Q110 68 120 74" stroke="#A67B5B" stroke-width="1" fill="none" opacity="0.3"/>
      <!-- 连接杆 -->
      <rect x="4" y="40" width="14" height="4" rx="1" fill="#64748B"/>
      <text x="60" y="97" text-anchor="middle" fill="#A67B5B" font-size="8" font-family="Inter,sans-serif">旋耕机</text>
    </svg>

    <!-- 播种机 -->
    <svg v-else-if="type === 'seeder'" viewBox="0 0 120 100" fill="none">
      <rect width="120" height="100" rx="4" fill="#0F1A10"/>
      <!-- 种子箱 -->
      <rect x="30" y="22" width="60" height="18" rx="3" fill="#131C26" stroke="#22C55E" stroke-width="1"/>
      <!-- 种子 -->
      <circle cx="48" cy="30" r="2.5" fill="#4ADE80" opacity="0.6"/>
      <circle cx="60" cy="28" r="2" fill="#4ADE80" opacity="0.5"/>
      <circle cx="72" cy="30" r="2.5" fill="#4ADE80" opacity="0.6"/>
      <!-- 排种管 -->
      <line x1="42" y1="40" x2="42" y2="60" stroke="#22C55E" stroke-width="1" opacity="0.5"/>
      <line x1="60" y1="40" x2="60" y2="60" stroke="#22C55E" stroke-width="1" opacity="0.5"/>
      <line x1="78" y1="40" x2="78" y2="60" stroke="#22C55E" stroke-width="1" opacity="0.5"/>
      <!-- 开沟器 -->
      <path d="M36 60 L42 70 L48 60" stroke="#22C55E" stroke-width="1.2" fill="none"/>
      <path d="M54 60 L60 70 L66 60" stroke="#22C55E" stroke-width="1.2" fill="none"/>
      <path d="M72 60 L78 70 L84 60" stroke="#22C55E" stroke-width="1.2" fill="none"/>
      <!-- 轮子 -->
      <circle cx="20" cy="65" r="9" fill="#111827" stroke="#22C55E" stroke-width="1.5"/>
      <circle cx="100" cy="65" r="9" fill="#111827" stroke="#22C55E" stroke-width="1.5"/>
      <!-- 播种 -->
      <circle cx="42" cy="74" r="1.5" fill="#4ADE80" opacity="0.5"/>
      <circle cx="60" cy="75" r="1.5" fill="#4ADE80" opacity="0.5"/>
      <circle cx="78" cy="74" r="1.5" fill="#4ADE80" opacity="0.5"/>
      <text x="60" y="97" text-anchor="middle" fill="#22C55E" font-size="8" font-family="Inter,sans-serif">精量播种机</text>
    </svg>

    <!-- 保水型 -->
    <svg v-else-if="type === 'decomposer-water'" viewBox="0 0 120 100" fill="none">
      <rect width="120" height="100" rx="4" fill="#081028"/>
      <path d="M30 50 Q40 20 60 30 Q80 40 90 50" fill="none" stroke="#3B82F6" stroke-width="2" opacity="0.6"/>
      <path d="M20 56 Q40 32 60 42 Q80 52 100 56" fill="none" stroke="#60A5FA" stroke-width="1.5" opacity="0.4"/>
      <circle cx="60" cy="44" r="16" fill="none" stroke="#3B82F6" stroke-width="1.2"/>
      <circle cx="60" cy="44" r="8" fill="#3B82F6" opacity="0.3"/>
      <text x="60" y="80" text-anchor="middle" fill="#60A5FA" font-size="9" font-family="Inter,sans-serif">H₂O</text>
      <text x="60" y="97" text-anchor="middle" fill="#60A5FA" font-size="8" font-family="Inter,sans-serif">保水腐解</text>
    </svg>

    <!-- 增肥型 -->
    <svg v-else-if="type === 'decomposer-rich'" viewBox="0 0 120 100" fill="none">
      <rect width="120" height="100" rx="4" fill="#1F1808"/>
      <circle cx="60" cy="34" r="20" fill="#D97706" opacity="0.12" stroke="#D97706" stroke-width="1.2"/>
      <path d="M60 14 L64 28 L78 28 L67 37 L71 51 L60 43 L49 51 L53 37 L42 28 L56 28 Z" fill="#D97706" opacity="0.6"/>
      <rect x="20" y="60" width="28" height="16" rx="3" fill="#2D1F08" stroke="#D97706" stroke-width="1" opacity="0.5"/>
      <rect x="56" y="58" width="28" height="18" rx="3" fill="#2D1F08" stroke="#D97706" stroke-width="1" opacity="0.5"/>
      <rect x="86" y="60" width="20" height="16" rx="3" fill="#2D1F08" stroke="#D97706" stroke-width="1" opacity="0.5"/>
      <text x="60" y="97" text-anchor="middle" fill="#D97706" font-size="8" font-family="Inter,sans-serif">增肥腐解</text>
    </svg>

    <!-- 默认 -->
    <svg v-else viewBox="0 0 120 100" fill="none">
      <rect width="120" height="100" rx="4" fill="#0C1117"/>
      <circle cx="60" cy="44" r="20" fill="none" stroke="#22C55E" stroke-width="1.5"/>
      <text x="60" y="48" text-anchor="middle" fill="#22C55E" font-size="22" font-family="Inter,sans-serif"><Wheat :size="16" /></text>
      <text x="60" y="80" text-anchor="middle" fill="#4ADE80" font-size="8" font-family="Inter,sans-serif">农用产品</text>
    </svg>
  </div>
</template>

<script setup>
import { Wheat } from 'lucide-vue-next'
defineProps({
  type: { type: String, default: 'default' },
  photo: { type: String, default: '' },
})
</script>

<style scoped>
.prod-img {
  width: 140px; height: 110px; flex-shrink: 0;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--surface-100);
}
.prod-img svg {
  width: 100%; height: 100%; display: block;
}
.prod-photo {
  width: 100%; height: 100%; object-fit: cover; display: block;
}
</style>
