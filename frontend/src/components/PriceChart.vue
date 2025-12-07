<script setup lang="ts">
import { defineProps, computed } from 'vue'
import { useI18n } from 'vue-i18n'

type PriceRow = {
  provider_name: string
  price_in: number
  price_out: number
  uptime: number
}

const props = defineProps<{ prices: PriceRow[]; loading: boolean }>()
const { t } = useI18n()

const normalized = computed(() => {
  const sorted = [...props.prices].sort((a, b) => a.price_in - b.price_in)
  const maxPrice = Math.max(...sorted.map(p => p.price_in), 0.000001)
  return sorted.slice(0, 12).map(p => ({
    ...p,
    barWidth: Math.max(8, (p.price_in / maxPrice) * 100),
    uptime: p.uptime || 0
  }))
})
</script>

<template>
  <div class="space-y-2">
    <el-skeleton v-if="loading" :rows="4" animated />
    <div v-else-if="!props.prices.length" class="text-center text-gray-400 py-10">{{ t('home.select_model_hint') }}</div>
    <div v-else class="space-y-3">
      <div v-for="row in normalized" :key="row.provider_name" class="bg-gray-50 p-3 rounded">
        <div class="flex justify-between text-sm font-semibold">
          <span>{{ row.provider_name }}</span>
          <span class="font-mono">{{ row.price_in.toFixed(6) }}</span>
        </div>
        <div class="h-3 mt-2 bg-white border rounded overflow-hidden">
          <div class="h-full bg-gradient-to-r from-blue-500 to-indigo-600" :style="{ width: row.barWidth + '%' }"></div>
        </div>
        <div class="flex justify-between text-xs text-gray-500 mt-1">
          <span>{{ t('table.uptime') }} {{ row.uptime }}%</span>
          <span>{{ t('table.output') }} {{ (row.price_out || 0).toFixed(6) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
