<script setup lang="ts">
import { defineProps } from 'vue'
import { useI18n } from 'vue-i18n'

interface PriceRow {
  provider_name: string
  provider_score: number
  uptime: number
  original_currency: string
  price_in: number
  price_out: number
  cache_hit_input_price?: number | null
  cache_hit_output_price?: number | null
  verified_at: string
  proof: string
}

defineProps<{
  prices: PriceRow[],
  loading: boolean
}>()

const { t } = useI18n()

const formatPrice = (val: number) => {
  return val.toFixed(6)
}
</script>

<template>
  <el-table :data="prices" v-loading="loading" style="width: 100%" stripe>
    <el-table-column :label="t('table.provider')" min-width="180">
      <template #default="{ row }">
        <div class="font-bold">{{ row.provider_name }}</div>
        <div class="text-xs text-gray-500">
          {{ t('table.uptime') }}: {{ row.uptime }}%
        </div>
      </template>
    </el-table-column>
    
    <el-table-column :label="t('table.reputation')" width="140">
      <template #default="{ row }">
        <el-rate
          v-model="row.provider_score"
          disabled
          show-score
          text-color="#ff9900"
        />
      </template>
    </el-table-column>

    <el-table-column :label="t('table.input')" min-width="150" sortable prop="price_in">
      <template #default="{ row }">
        <span class="font-mono">{{ formatPrice(row.price_in) }}</span>
      </template>
    </el-table-column>

    <el-table-column :label="t('table.output')" min-width="150" sortable prop="price_out">
      <template #default="{ row }">
        <span class="font-mono">{{ formatPrice(row.price_out) }}</span>
      </template>
    </el-table-column>

    <el-table-column :label="t('table.cache_hit_input')" min-width="160">
      <template #default="{ row }">
        <span class="font-mono" v-if="row.cache_hit_input_price != null">{{ formatPrice(row.cache_hit_input_price) }}</span>
        <span v-else class="text-gray-400">{{ t('home.no_data') }}</span>
      </template>
    </el-table-column>

    <el-table-column :label="t('table.cache_hit_output')" min-width="160">
      <template #default="{ row }">
        <span class="font-mono" v-if="row.cache_hit_output_price != null">{{ formatPrice(row.cache_hit_output_price) }}</span>
        <span v-else class="text-gray-400">{{ t('home.no_data') }}</span>
      </template>
    </el-table-column>

    <el-table-column :label="t('table.verified')" width="120">
      <template #default="{ row }">
        <div v-if="row.verified_at" class="text-green-600 text-sm">
          {{ t('table.verified') }}
        </div>
        <div v-else class="text-gray-400 text-sm">{{ t('table.no') }}</div>
      </template>
    </el-table-column>

    <el-table-column :label="t('table.proof')" width="100">
      <template #default="{ row }">
        <el-link v-if="row.proof" :href="'/static/' + row.proof" target="_blank" type="primary">{{ t('table.view') }}</el-link>
      </template>
    </el-table-column>
  </el-table>
</template>
