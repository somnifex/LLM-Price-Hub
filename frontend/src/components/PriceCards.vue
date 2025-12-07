<script setup lang="ts">
import { defineProps, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { StarFilled } from '@element-plus/icons-vue'

type PriceRow = {
  provider_name: string
  provider_model_name?: string
  provider_score: number
  uptime: number
  original_currency: string
  price_in: number
  price_out: number
  cache_hit_input_price?: number | null
  cache_hit_output_price?: number | null
  verified_at?: string | null
  proof?: string | null
}

const props = defineProps<{ prices: PriceRow[]; loading: boolean }>()
const { t } = useI18n()

const sorted = computed(() => [...props.prices].sort((a, b) => a.price_in - b.price_in))
</script>

<template>
  <div>
    <el-skeleton v-if="loading" :rows="4" animated />
    <div v-else-if="!sorted.length" class="text-center text-gray-400 py-10">{{ t('home.select_model_hint') }}</div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <el-card v-for="row in sorted" :key="row.provider_name" shadow="hover">
        <div class="flex items-center justify-between mb-2">
          <div>
            <div class="text-lg font-bold">{{ row.provider_name }}</div>
            <div v-if="row.provider_model_name" class="text-xs text-gray-500">{{ row.provider_model_name }}</div>
          </div>
          <el-tag type="success" size="small">{{ t('table.uptime') }}: {{ row.uptime }}%</el-tag>
        </div>
        <div class="flex items-center gap-2 mb-3 text-amber-500">
          <el-icon><StarFilled /></el-icon>
          <span class="text-sm">{{ (row.provider_score || 0).toFixed(1) }}</span>
        </div>
        <div class="space-y-1 font-mono">
          <div class="flex justify-between text-sm">
            <span>{{ t('table.input') }}</span>
            <span>{{ (row.price_in || 0).toFixed(6) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span>{{ t('table.output') }}</span>
            <span>{{ (row.price_out || 0).toFixed(6) }}</span>
          </div>
          <div class="flex justify-between text-sm" v-if="row.cache_hit_input_price != null">
            <span>{{ t('table.cache_hit_input') }}</span>
            <span>{{ (row.cache_hit_input_price || 0).toFixed(6) }}</span>
          </div>
          <div class="flex justify-between text-sm" v-if="row.cache_hit_output_price != null">
            <span>{{ t('table.cache_hit_output') }}</span>
            <span>{{ (row.cache_hit_output_price || 0).toFixed(6) }}</span>
          </div>
          <div class="flex justify-between text-xs text-gray-500">
            <span>{{ t('table.verified') }}</span>
            <span>{{ row.verified_at ? t('table.verified') : t('table.no') }}</span>
          </div>
        </div>
        <div v-if="row.proof" class="mt-3 text-right">
          <el-link :href="row.proof.startsWith('http') ? row.proof : '/' + row.proof" target="_blank" type="primary">{{ t('table.view') }}</el-link>
        </div>
      </el-card>
    </div>
  </div>
</template>
