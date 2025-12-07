<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useI18n } from 'vue-i18n'
import { useSettingsStore } from '@/stores/settings'

const { t } = useI18n()
const router = useRouter()
const settingsStore = useSettingsStore()

// Data
const models = ref<Array<{id: number, name: string, vendor?: string}>>([])
const providers = ref<Array<{id: number, name: string, status?: string}>>([])
const loading = ref(false)

// Provider form
const providerMode = ref<'existing' | 'new'>('existing')
const formProvider = ref({
  provider_id: null as number | null,
  provider_name: '',
  provider_website: '',
  openai_base_url: '',
  gemini_base_url: '',
  claude_base_url: '',
  submit_provider_for_review: false,
  provider_proof_type: 'text',
  provider_proof_content: ''
})

// Model price rows
type PriceRow = {
  mode: 'existing' | 'new'
  standard_model_id: number | null
  new_model_name: string
  new_model_vendor: string
  provider_model_name: string
  price_in: number
  price_out: number
  cache_hit_input_price: number | null
  cache_hit_output_price: number | null
  currency: string
  proof_type: 'text' | 'url'
  proof_content: string
}

const priceRows = ref<PriceRow[]>([
  {
    mode: 'existing',
    standard_model_id: null,
    new_model_name: '',
    new_model_vendor: '',
    provider_model_name: '',
    price_in: 0,
    price_out: 0,
    cache_hit_input_price: null,
    cache_hit_output_price: null,
    currency: 'USD',
    proof_type: 'text',
    proof_content: ''
  }
])

const currencyOptions = computed(() => {
  const list = settingsStore.currencies
  if (!list || !list.length) {
    return [
      { label: 'USD', value: 'USD' },
      { label: 'CNY', value: 'CNY' },
      { label: 'EUR', value: 'EUR' },
    ]
  }
  const commons = list.filter((c: any) => c.is_common)
  const rest = list.filter((c: any) => !c.is_common)
  const ordered = [...commons, ...rest]
  return ordered.map((c: any) => {
    const flag = c.flag ? `${c.flag} ` : ''
    return { label: `${flag}${c.code}`, value: c.code }
  })
})

const addRow = () => {
  priceRows.value.push({
    mode: 'existing',
    standard_model_id: null,
    new_model_name: '',
    new_model_vendor: '',
    provider_model_name: '',
    price_in: 0,
    price_out: 0,
    cache_hit_input_price: null,
    cache_hit_output_price: null,
    currency: settingsStore.userSettings.default_currency || 'USD',
    proof_type: 'text',
    proof_content: ''
  })
}

const removeRow = (idx: number) => {
  if (priceRows.value.length === 1) return
  priceRows.value.splice(idx, 1)
}

const fetchModels = async () => {
  try {
    const res = await api.get('/prices/models')
    models.value = res.data
  } catch {
    // Silent fail
  }
}

const fetchProviders = async () => {
  try {
    // Get public providers + user's own providers
    const [publicRes, userRes] = await Promise.all([
      api.get('/config/providers'),
      api.get('/user/providers').catch(() => ({ data: [] }))
    ])
    providers.value = [...publicRes.data, ...userRes.data]
  } catch {
    // Silent fail
  }
}

const submit = async () => {
  // Provider validation
  if (providerMode.value === 'existing' && !formProvider.value.provider_id) {
    ElMessage.error(t('submit.select_provider_error'))
    return
  }
  if (providerMode.value === 'new' && !formProvider.value.provider_name) {
    ElMessage.error(t('submit.enter_provider_name'))
    return
  }

  // Rows validation
  for (const row of priceRows.value) {
    if (row.mode === 'existing' && !row.standard_model_id) {
      ElMessage.error(t('submit.select_model_error'))
      return
    }
    if (row.mode === 'new' && !row.new_model_name) {
      ElMessage.error(t('submit.enter_model_name'))
      return
    }
    if (!row.proof_content) {
      ElMessage.error(t('submit.proof_required'))
      return
    }
  }

  loading.value = true
  try {
    const payload = {
      provider_id: providerMode.value === 'existing' ? formProvider.value.provider_id : null,
      provider_name: providerMode.value === 'new' ? formProvider.value.provider_name : undefined,
      provider_website: formProvider.value.provider_website,
      openai_base_url: formProvider.value.openai_base_url,
      gemini_base_url: formProvider.value.gemini_base_url,
      claude_base_url: formProvider.value.claude_base_url,
      submit_provider_for_review: formProvider.value.submit_provider_for_review,
      provider_proof_type: formProvider.value.provider_proof_type,
      provider_proof_content: formProvider.value.provider_proof_content,
      prices: priceRows.value.map(r => ({
        standard_model_id: r.mode === 'existing' ? r.standard_model_id : null,
        new_model_name: r.mode === 'new' ? r.new_model_name : null,
        new_model_vendor: r.mode === 'new' ? r.new_model_vendor : null,
        provider_model_name: r.provider_model_name,
        price_in: r.price_in,
        price_out: r.price_out,
        cache_hit_input_price: r.cache_hit_input_price,
        cache_hit_output_price: r.cache_hit_output_price,
        currency: r.currency,
        proof_type: r.proof_type,
        proof_content: r.proof_content
      }))
    }

    await api.post('/prices/submit-batch', payload)
    ElMessage.success(t('submit.success'))
    router.push('/admin')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || t('submit.failed')
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await settingsStore.fetchCurrencies()
  await settingsStore.fetchUserSettings()
  // Update existing rows to default currency if available
  const def = settingsStore.userSettings.default_currency || 'USD'
  priceRows.value = priceRows.value.map(r => ({ ...r, currency: def }))
  fetchModels()
  fetchProviders()
})
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <span class="text-xl font-bold">{{ t('submit.title') }}</span>
          <el-button link type="primary" @click="addRow">{{ t('submit.add_row') }}</el-button>
        </div>
      </template>

      <el-form label-position="top">
        <!-- Provider Section -->
        <div class="mb-6">
          <h3 class="text-lg font-semibold mb-4 border-b pb-2">{{ t('submit.provider_section') }}</h3>

          <el-radio-group v-model="providerMode" class="mb-4">
            <el-radio value="existing">{{ t('submit.use_existing_provider') }}</el-radio>
            <el-radio value="new">{{ t('submit.create_new_provider') }}</el-radio>
          </el-radio-group>

          <template v-if="providerMode === 'existing'">
            <el-form-item :label="t('submit.select_provider')">
              <el-select v-model="formProvider.provider_id" class="w-full" filterable>
                <el-option v-for="p in providers" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </template>
          <template v-else>
            <el-form-item :label="t('submit.provider_name')">
              <el-input v-model="formProvider.provider_name" :placeholder="t('submit.provider_name_placeholder')" />
            </el-form-item>
            <el-form-item :label="t('submit.provider_website')">
              <el-input v-model="formProvider.provider_website" placeholder="https://example.com" />
            </el-form-item>

            <el-collapse class="mb-4">
              <el-collapse-item :title="t('submit.api_base_urls')">
                <el-form-item label="OpenAI Base URL">
                  <el-input v-model="formProvider.openai_base_url" placeholder="https://api.openai.com/v1" />
                </el-form-item>
                <el-form-item label="Gemini Base URL">
                  <el-input v-model="formProvider.gemini_base_url" />
                </el-form-item>
                <el-form-item label="Claude Base URL">
                  <el-input v-model="formProvider.claude_base_url" />
                </el-form-item>
              </el-collapse-item>
            </el-collapse>

            <el-form-item>
              <el-switch v-model="formProvider.submit_provider_for_review" :active-text="t('submit.submit_provider_public')" />
            </el-form-item>

            <template v-if="formProvider.submit_provider_for_review">
              <el-form-item :label="t('submit.provider_proof')">
                <el-radio-group v-model="formProvider.provider_proof_type">
                  <el-radio value="text">{{ t('submit.proof_text') }}</el-radio>
                  <el-radio value="url">{{ t('submit.proof_url') }}</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item>
                <el-input
                  v-model="formProvider.provider_proof_content"
                  :type="formProvider.provider_proof_type === 'text' ? 'textarea' : 'text'"
                  :placeholder="formProvider.provider_proof_type === 'url' ? 'https://docs.example.com/pricing' : t('submit.proof_description')"
                />
              </el-form-item>
            </template>
          </template>
        </div>

        <!-- Model Price Rows -->
        <div class="space-y-6">
          <div
            v-for="(row, idx) in priceRows"
            :key="idx"
            class="p-4 border rounded-lg bg-gray-50"
          >
            <div class="flex justify-between items-center mb-3">
              <h4 class="font-semibold">{{ t('submit.row_title') }} #{{ idx + 1 }}</h4>
              <el-button link type="danger" @click="removeRow(idx)" :disabled="priceRows.length === 1">{{ t('submit.remove_row') }}</el-button>
            </div>

            <el-radio-group v-model="row.mode" class="mb-3">
              <el-radio value="existing">{{ t('submit.use_existing_model') }}</el-radio>
              <el-radio value="new">{{ t('submit.request_new_model') }}</el-radio>
            </el-radio-group>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <template v-if="row.mode === 'existing'">
                <el-form-item :label="t('submit.select_model')">
                  <el-select v-model="row.standard_model_id" class="w-full" filterable>
                    <el-option v-for="m in models" :key="m.id" :label="m.name + (m.vendor ? ' (' + m.vendor + ')' : '')" :value="m.id" />
                  </el-select>
                </el-form-item>
              </template>
              <template v-else>
                <el-form-item :label="t('submit.new_model_name')">
                  <el-input v-model="row.new_model_name" :placeholder="t('submit.new_model_name_placeholder')" />
                </el-form-item>
                <el-form-item :label="t('submit.new_model_vendor')">
                  <el-input v-model="row.new_model_vendor" :placeholder="t('submit.new_model_vendor_placeholder')" />
                </el-form-item>
              </template>
            </div>

            <el-form-item :label="t('submit.provider_model_name')">
              <el-input v-model="row.provider_model_name" :placeholder="t('submit.provider_model_name_placeholder')" />
            </el-form-item>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <el-form-item :label="t('submit.price_in')">
                <el-input-number v-model="row.price_in" :min="0" :step="0.0001" controls-position="right" class="w-full" />
              </el-form-item>
              <el-form-item :label="t('submit.price_out')">
                <el-input-number v-model="row.price_out" :min="0" :step="0.0001" controls-position="right" class="w-full" />
              </el-form-item>
              <el-form-item :label="t('submit.cache_hit_input')">
                <el-input-number v-model="row.cache_hit_input_price" :min="0" :step="0.0001" controls-position="right" class="w-full" />
              </el-form-item>
              <el-form-item :label="t('submit.cache_hit_output')">
                <el-input-number v-model="row.cache_hit_output_price" :min="0" :step="0.0001" controls-position="right" class="w-full" />
              </el-form-item>
            </div>

            <el-form-item :label="t('submit.currency')">
              <el-select v-model="row.currency" class="w-full" filterable>
                <el-option v-for="opt in currencyOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>

            <el-form-item :label="t('submit.proof_type')">
              <el-radio-group v-model="row.proof_type">
                <el-radio value="text">{{ t('submit.proof_text') }}</el-radio>
                <el-radio value="url">{{ t('submit.proof_url') }}</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="row.proof_content"
                :type="row.proof_type === 'text' ? 'textarea' : 'text'"
                :placeholder="row.proof_type === 'url' ? 'https://example.com/proof' : t('submit.proof_description')"
              />
            </el-form-item>
          </div>
        </div>

        <el-form-item class="mt-6">
          <el-button type="primary" :loading="loading" @click="submit">{{ t('submit.submit_btn') }}</el-button>
          <el-button @click="router.back()">{{ t('submit.cancel_btn') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
