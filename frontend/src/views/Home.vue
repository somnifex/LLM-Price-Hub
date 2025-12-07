<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/api'
import PriceTable from '@/components/PriceTable.vue'
import PriceCards from '@/components/PriceCards.vue'
import PriceChart from '@/components/PriceChart.vue'
import { Search, List, Grid, TrendCharts } from '@element-plus/icons-vue'
import { useSettingsStore } from '@/stores/settings'

const { t } = useI18n()
const settingsStore = useSettingsStore()
const models = ref<Array<{id: number, name: string, vendor: string}>>([])
const selectedModel = ref<number | null>(null)
const targetCurrency = ref('USD')
const prices = ref<Array<any>>([])
const loading = ref(false)
const allowedModes = ['table', 'cards', 'chart'] as const
const displayMode = ref<typeof allowedModes[number]>('table')
const publicSettings = ref<Record<string, string>>({})

const currencies = computed(() => {
  if (settingsStore.userSettings.preferred_currencies.length > 0) {
    return settingsStore.userSettings.preferred_currencies
  }
  return ['USD', 'CNY', 'EUR']
})

const currentViewComponent = computed(() => {
  switch (displayMode.value) {
    case 'cards': return PriceCards
    case 'chart': return PriceChart
    default: return PriceTable
  }
})

const fetchModels = async () => {
  try {
    const res = await api.get('/models')
    models.value = res.data
  } catch {
    // Silent fail - models will be empty
  }
}

const fetchPublicSettings = async () => {
  try {
    const res = await api.get('/config/public-settings')
    publicSettings.value = res.data || {}
    const mode = res.data?.home_display_mode
    if (mode && allowedModes.includes(mode)) {
      // Use server default only when no saved preference exists
      if (!localStorage.getItem('homeDisplayMode')) {
        displayMode.value = mode
      }
    }
  } catch {
    // ignore
  }
}

const fetchPrices = async () => {
  if (!selectedModel.value) return
  loading.value = true
  try {
    const res = await api.get(`/prices/compare/${selectedModel.value}`, {
      params: { target_currency: targetCurrency.value }
    })
    prices.value = res.data
  } catch {
    // Silent fail - prices will be empty
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const saved = localStorage.getItem('homeDisplayMode')
  if (saved && allowedModes.includes(saved as typeof allowedModes[number])) {
    displayMode.value = saved as typeof allowedModes[number]
  }
  
  await settingsStore.fetchCurrencies()
  await settingsStore.fetchUserSettings()
  targetCurrency.value = settingsStore.userSettings.default_currency

  fetchModels()
  fetchPublicSettings()
})

watch(displayMode, (val) => {
  localStorage.setItem('homeDisplayMode', val)
})
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)]">
    <!-- Hero Section -->
    <div class="relative bg-white border-b border-gray-100 overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-primary-50 to-secondary-50 opacity-50"></div>
      <div class="absolute inset-0" style="background-image: radial-gradient(#e5e7eb 1px, transparent 1px); background-size: 24px 24px; mask-image: linear-gradient(180deg, white, rgba(255,255,255,0));"></div>
      
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 text-center">
        <h1 class="text-5xl md:text-6xl font-extrabold tracking-tight text-gray-900 mb-6">
          <span class="bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-primary-800">
            {{ t('home.title') }}
          </span>
        </h1>
        <p class="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
          {{ t('home.subtitle') }}
        </p>

        <!-- Search/Filter Bar -->
        <div class="max-w-4xl mx-auto bg-white p-2 rounded-2xl shadow-xl shadow-primary-100/50 border border-gray-100 flex flex-col md:flex-row gap-2">
          <div class="flex-1 relative group flex items-center">
            <div class="absolute left-4 z-10 flex items-center pointer-events-none">
              <el-icon class="text-gray-400 text-xl"><Search /></el-icon>
            </div>
            <el-select 
              v-model="selectedModel" 
              :placeholder="t('home.model_label')" 
              class="w-full custom-select-hero with-icon" 
              filterable 
              size="large"
              @change="fetchPrices"
            >
              <el-option
                v-for="item in models"
                :key="item.id"
                :label="item.name + ' (' + item.vendor + ')'"
                :value="item.id"
              />
            </el-select>
          </div>
          
          <div class="w-full md:w-48 border-t md:border-t-0 md:border-l border-gray-100">
             <el-select v-model="targetCurrency" size="large" class="w-full custom-select-hero" @change="fetchPrices">
              <el-option v-for="curr in currencies" :key="curr" :label="t('currency.' + curr)" :value="curr" />
            </el-select>
          </div>
        </div>
      </div>
    </div>

    <!-- Content Section -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <!-- View Toggles -->
      <div class="flex justify-end mb-6">
        <div class="bg-gray-100 p-1 rounded-lg flex gap-1">
          <button 
            v-for="mode in allowedModes" 
            :key="mode"
            @click="displayMode = mode"
            :class="['px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2', displayMode === mode ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700']"
          >
            <el-icon v-if="mode === 'table'"><List /></el-icon>
            <el-icon v-else-if="mode === 'cards'"><Grid /></el-icon>
            <el-icon v-else><TrendCharts /></el-icon>
            <span class="capitalize">{{ t('home.display_' + mode) }}</span>
          </button>
        </div>
      </div>

      <!-- Results -->
      <div v-loading="loading" class="min-h-[400px]">
        <div v-if="!selectedModel" class="text-center py-20">
          <div class="w-16 h-16 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-4 text-primary-500">
            <el-icon :size="32"><Search /></el-icon>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">{{ t('home.select_model_hint') }}</h3>
        </div>

        <template v-else>
          <Transition name="fade" mode="out-in">
            <component :is="currentViewComponent" :prices="prices" :loading="loading" :currency="targetCurrency" />
          </Transition>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-select-hero {
  --el-select-border-color-hover: transparent;
  --el-select-input-focus-border-color: transparent;
}

.custom-select-hero :deep(.el-input__wrapper),
.custom-select-hero :deep(.el-select__wrapper) {
  box-shadow: none !important;
  background-color: transparent;
}

.custom-select-hero.with-icon :deep(.el-input__wrapper),
.custom-select-hero.with-icon :deep(.el-select__wrapper) {
  padding-left: 50px;
}

.custom-select-hero :deep(.el-input__inner) {
  height: 48px;
  font-size: 1.125rem;
  color: #374151;
}
</style>
