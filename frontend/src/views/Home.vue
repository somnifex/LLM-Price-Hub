<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/api'
import PriceTable from '@/components/PriceTable.vue'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()
const models = ref<Array<{id: number, name: string, vendor: string}>>([])
const selectedModel = ref<number | null>(null)
const targetCurrency = ref('USD')
const currencies = ref(['USD', 'CNY', 'EUR']) // Could fetch from API
const prices = ref<Array<any>>([])
const loading = ref(false)

const fetchModels = async () => {
  try {
    const res = await api.get('/models')
    models.value = res.data
  } catch {
    // Silent fail - models will be empty
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

onMounted(() => {
  fetchModels()
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <div class="text-center mb-10">
      <h1 class="text-4xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
        {{ t('home.title') }}
      </h1>
      <p class="text-gray-600 text-lg">{{ t('home.subtitle') }}</p>
    </div>

    <!-- Controls -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col md:flex-row gap-4 items-end mb-8">
      <div class="flex-1">
        <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('home.model_label') }}</label>
        <el-select v-model="selectedModel" :placeholder="t('home.model_label')" class="w-full" filterable @change="fetchPrices">
          <el-option
            v-for="item in models"
            :key="item.id"
            :label="item.name + ' (' + item.vendor + ')'"
            :value="item.id"
          />
        </el-select>
      </div>

      <div class="w-32">
        <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('home.currency_label') }}</label>
        <el-select v-model="targetCurrency" @change="fetchPrices">
          <el-option v-for="c in currencies" :key="c" :label="c" :value="c" />
        </el-select>
      </div>

      <el-button type="primary" size="large" @click="fetchPrices" :loading="loading" class="h-[40px]">
        {{ t('home.search') }}
      </el-button>
      
      <router-link to="/submit">
        <el-button size="large">{{ t('nav.submit') }}</el-button>
      </router-link>

      <router-link to="/admin" v-if="authStore.isSuperAdmin">
        <el-button type="warning" size="large">{{ t('home.super_admin') }}</el-button>
      </router-link>
    </div>

    <!-- Results -->
    <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden min-h-[400px]">
      <div v-if="!selectedModel" class="flex items-center justify-center h-full min-h-[300px] text-gray-400">
        {{ t('home.select_model_hint') }}
      </div>
      <PriceTable v-else :prices="prices" :loading="loading" />
    </div>
  </div>
</template>
