<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Model {
  id: number;
  name: string;
  vendor?: string;
  official_currency: string;
  official_input_price?: number;
  official_output_price?: number;
  is_featured: boolean;
  rank_hint?: number;
  popularity_score: number;
}

// Pending data
const pendingPrices = ref([])
const pendingProviders = ref([])
const pendingModels = ref([])
const models = ref<Model[]>([])

// Loading states
const pricesLoading = ref(false)
const providersLoading = ref(false)
const modelsLoading = ref(false)
const modelListLoading = ref(false)
const currenciesLoading = ref(false)
const modelSaving = ref(false)
const editSaving = ref(false)

// Active tab
const activeTab = ref('prices')

// Currencies for official price entries
const currencies = ref([])
const currencyOptions = computed(() => {
    if (!currencies.value.length) {
        return [{ label: 'USD', value: 'USD' }]
    }
    return currencies.value.map((c: any) => ({ label: c.code, value: c.code }))
})

// Standard model form state
const modelFormDefaults = {
    name: '',
    vendor: '',
    official_currency: 'USD',
    official_input_price: null as number | null,
    official_output_price: null as number | null,
    is_featured: false,
    rank_hint: null as number | null,
}

const newModel = ref({ ...modelFormDefaults })
const editingModel = ref<any | null>(null)
const editDialogVisible = ref(false)
const bulkText = ref('')
const bulkImporting = ref(false)
const bulkDeleteLoading = ref(false)
const selectedModelIds = ref<number[]>([])
const selectedCount = computed(() => selectedModelIds.value.length)

const resetNewModel = () => {
    newModel.value = { ...modelFormDefaults }
}

const normalizeModelPayload = (payload: any) => {
    const toNumberOrNull = (value: any) => {
        if (value === '' || value === null || value === undefined) return null
        const num = Number(value)
        return Number.isNaN(num) ? null : num
    }

    return {
        name: payload.name?.trim(),
        vendor: payload.vendor?.trim() || null,
        official_currency: payload.official_currency || 'USD',
        official_input_price: toNumberOrNull(payload.official_input_price),
        official_output_price: toNumberOrNull(payload.official_output_price),
        is_featured: Boolean(payload.is_featured),
        rank_hint: toNumberOrNull(payload.rank_hint),
    }
}

const selectionChanged = (rows: any[]) => {
    selectedModelIds.value = rows.map((row: any) => row.id)
}

const parseBulkModels = () => {
    const lines = bulkText.value
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(Boolean)

    if (!lines.length) {
        throw new Error(t('admin.bulk_import_empty'))
    }

    const truthy = (value: any) => {
        if (!value) return false
        return ['1', 'true', 'yes', 'y', 'on'].includes(String(value).toLowerCase())
    }
    const toNumber = (value: any) => {
        if (value === undefined || value === null || value === '') return null
        const num = Number(value)
        return Number.isNaN(num) ? null : num
    }

    return lines.map((line, idx) => {
        const parts = line.split(/[,|\t]/).map(p => p.trim())
        const [name, vendor, currency, input, output, featured, rank] = parts
        if (!name) {
            throw new Error(t('admin.bulk_import_format_error', { line: idx + 1 }))
        }
        return {
            name,
            vendor: vendor || null,
            official_currency: currency || 'USD',
            official_input_price: toNumber(input),
            official_output_price: toNumber(output),
            is_featured: truthy(featured),
            rank_hint: toNumber(rank),
        }
    })
}

const bulkImportModels = async () => {
    let items: any[] = []
    try {
        items = parseBulkModels()
    } catch (err: any) {
        ElMessage.error(err.message || t('admin.action_failed'))
        return
    }

    bulkImporting.value = true
    try {
        const res = await api.post('/admin/models/bulk', { items })
        const created = res.data?.created || 0
        const updated = res.data?.updated || 0
        ElMessage.success(t('admin.bulk_import_result', { created, updated }))
        bulkText.value = ''
        fetchModels()
    } catch (e) {
        ElMessage.error(t('admin.action_failed'))
    } finally {
        bulkImporting.value = false
    }
}

const deleteSelectedModels = async () => {
    if (!selectedModelIds.value.length) {
        ElMessage.info(t('admin.no_models_selected'))
        return
    }
    try {
        await ElMessageBox.confirm(
            t('admin.confirm_bulk_delete', { count: selectedModelIds.value.length }),
            t('common.warning'),
            { type: 'warning' }
        )
    } catch (e: any) {
        if (e === 'cancel' || e?.action === 'cancel') return
    }

    bulkDeleteLoading.value = true
    try {
        await api.delete('/admin/models/bulk', { data: { ids: selectedModelIds.value } })
        ElMessage.success(t('admin.bulk_delete_success'))
        selectedModelIds.value = []
        fetchModels()
    } catch (e) {
        ElMessage.error(t('admin.action_failed'))
    } finally {
        bulkDeleteLoading.value = false
    }
}

// Fetch functions
const fetchPendingPrices = async () => {
  pricesLoading.value = true
  try {
    const res = await api.get('/admin/pending')
    pendingPrices.value = res.data
  } catch (e) {
    ElMessage.error(t('admin.failed_fetch_pending_prices'))
  } finally {
    pricesLoading.value = false
  }
}

const fetchPendingProviders = async () => {
  providersLoading.value = true
  try {
    const res = await api.get('/admin/providers/pending')
    pendingProviders.value = res.data
  } catch (e) {
    ElMessage.error(t('admin.failed_fetch_providers'))
  } finally {
    providersLoading.value = false
  }
}

const fetchPendingModels = async () => {
  modelsLoading.value = true
  try {
    const res = await api.get('/admin/model-requests/pending')
    pendingModels.value = res.data
  } catch (e) {
    ElMessage.error(t('admin.failed_fetch_models'))
  } finally {
    modelsLoading.value = false
  }
}

const fetchCurrencies = async () => {
    currenciesLoading.value = true
    try {
        const res = await api.get('/settings/currencies')
        currencies.value = res.data
    } catch (e) {
        // allow page to load even if currencies fail
    } finally {
        currenciesLoading.value = false
    }
}

const fetchModels = async () => {
  modelListLoading.value = true
  try {
    const res = await api.get('/admin/models')
    models.value = res.data
  } catch {
    // Silent fail
  } finally {
    modelListLoading.value = false
  }
}

// Action handlers
const handlePriceAction = async (id: number, action: 'approve' | 'reject') => {
  try {
    await api.post(`/admin/${action}/${id}`)
    ElMessage.success(action === 'approve' ? t('admin.price_approved') : t('admin.price_rejected'))
    fetchPendingPrices()
  } catch (e) {
    ElMessage.error(t('admin.action_failed'))
  }
}

const handleProviderAction = async (id: number, action: 'approve' | 'reject') => {
  try {
    await api.post(`/admin/providers/${id}/${action}`)
    ElMessage.success(action === 'approve' ? t('admin.provider_approved') : t('admin.provider_rejected'))
    fetchPendingProviders()
  } catch (e) {
    ElMessage.error(t('admin.action_failed'))
  }
}

const handleModelAction = async (id: number, action: 'approve' | 'reject') => {
  try {
    const path = action === 'approve' ? `/admin/model-requests/${id}/approve` : `/admin/model-requests/${id}/reject`
    const body = action === 'approve' ? {} : undefined
    await api.post(path, body)
    ElMessage.success(action === 'approve' ? t('admin.model_approved') : t('admin.model_rejected'))
    fetchPendingModels()
    fetchModels()
  } catch (e) {
    ElMessage.error(t('admin.action_failed'))
  }
}

// Model Management
const createModel = async () => {
  if(!newModel.value.name) return
  modelSaving.value = true
  try {
    const payload = normalizeModelPayload(newModel.value)
    await api.post('/admin/models', payload)
    ElMessage.success(t('admin.model_created'))
    resetNewModel()
    fetchModels()
  } catch (e) {
    ElMessage.error(t('admin.failed_create_model'))
  } finally {
    modelSaving.value = false
  }
}

const openEditModel = (model: any) => {
    editingModel.value = { ...model }
    editDialogVisible.value = true
}

const saveModelEdit = async () => {
    if (!editingModel.value) return
    editSaving.value = true
    try {
        const payload = normalizeModelPayload(editingModel.value)
        await api.put(`/admin/models/${editingModel.value.id}`, payload)
        ElMessage.success(t('admin.model_updated'))
        editDialogVisible.value = false
        fetchModels()
    } catch (e) {
        ElMessage.error(t('admin.action_failed'))
    } finally {
        editSaving.value = false
    }
}

const deleteModel = async (modelId: number) => {
    try {
        await ElMessageBox.confirm(
            t('admin.confirm_delete_model'),
            t('common.warning'),
            { type: 'warning' }
        )
        await api.delete(`/admin/models/${modelId}`)
        ElMessage.success(t('admin.model_deleted'))
        selectedModelIds.value = selectedModelIds.value.filter(id => id !== modelId)
        fetchModels()
    } catch (e: any) {
        if (e !== 'cancel') {
            ElMessage.error(t('admin.action_failed'))
        }
    }
}

onMounted(() => {
  fetchPendingPrices()
  fetchPendingProviders()
  fetchPendingModels()
  fetchModels()
  fetchCurrencies()
})
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="panel p-4">
        <p class="section-kicker mb-2">{{ t('admin.pending_prices') }}</p>
        <div class="flex items-end justify-between">
          <div>
            <div class="text-3xl font-extrabold text-secondary-900">{{ pendingPrices.length }}</div>
            <p class="muted-subtitle">{{ t('admin.pending_price_submissions') }}</p>
          </div>
          <span class="pill-accent">{{ t('table.provider') }}</span>
        </div>
      </div>
      <div class="panel p-4">
        <p class="section-kicker mb-2">{{ t('admin.pending_providers') }}</p>
        <div class="flex items-end justify-between">
          <div>
            <div class="text-3xl font-extrabold text-secondary-900">{{ pendingProviders.length }}</div>
            <p class="muted-subtitle">{{ t('admin.pending_provider_submissions') }}</p>
          </div>
          <span class="pill-accent">{{ t('admin.base_urls') }}</span>
        </div>
      </div>
      <div class="panel p-4">
        <p class="section-kicker mb-2">{{ t('admin.pending_models') }}</p>
        <div class="flex items-end justify-between">
          <div>
            <div class="text-3xl font-extrabold text-secondary-900">{{ pendingModels.length }}</div>
            <p class="muted-subtitle">{{ t('admin.pending_model_requests') }}</p>
          </div>
          <span class="pill-accent">{{ t('admin.manage_models') }}</span>
        </div>
      </div>
    </div>

    <div class="panel p-3 md:p-4">
      <el-tabs v-model="activeTab" type="card">
        <!-- Pending Prices Tab -->
        <el-tab-pane :label="t('admin.pending_prices')" name="prices">
          <div class="space-y-3">
            <div class="section-header">
              <div>
                <h3 class="text-xl font-semibold text-secondary-900">{{ t('admin.pending_price_submissions') }}</h3>
                <p class="muted-subtitle">{{ t('admin.pending_prices') }}</p>
              </div>
              <el-badge :value="pendingPrices.length" type="warning" />
            </div>
            
            <div v-if="pendingPrices.length === 0" class="flex items-center justify-between rounded-xl border border-dashed border-gray-200 bg-gray-50 px-4 py-3 text-gray-600">
              <span>{{ t('admin.no_pending_submissions') }}</span>
              <el-tag type="info" effect="plain">{{ t('admin.pending_prices') }}</el-tag>
            </div>
            <el-table v-else :data="pendingPrices" v-loading="pricesLoading" class="rounded-xl overflow-hidden">
              <el-table-column :label="t('table.provider')">
                <template #default="{ row }">
                  <div class="whitespace-normal break-words">{{ row.provider_name || '-' }}</div>
                </template>
              </el-table-column>
              <el-table-column :label="t('admin.standard_model')">
                <template #default="{ row }">
                  <div class="whitespace-normal break-words">{{ row.model_name || '-' }}</div>
                </template>
              </el-table-column>
              <el-table-column :label="t('admin.provider_model_name')">
                <template #default="{ row }">
                  <div class="whitespace-normal break-words text-sm">{{ row.provider_model_name || '-' }}</div>
                </template>
              </el-table-column>
              <el-table-column :label="t('admin.price')">
                <template #default="{ row }">
                  {{ row.input_price }} / {{ row.output_price }} {{ row.currency }}
                </template>
              </el-table-column>
              <el-table-column :label="t('table.proof')">
                <template #default="{ row }">
                  <span v-if="row.proof_type === 'text'" class="text-sm">{{ (row.proof_content || '').substring(0, 50) }}...</span>
                  <a v-else-if="row.proof_type === 'url'" :href="row.proof_content" target="_blank" class="text-primary-600 hover:text-primary-700">{{ t('admin.link') }}</a>
                  <a v-else-if="row.proof_img_path" :href="'/' + row.proof_img_path" target="_blank" class="text-primary-600 hover:text-primary-700">{{ t('admin.image') }}</a>
                </template>
              </el-table-column>
              <el-table-column :label="t('common.actions')" width="180">
                <template #default="{ row }">
                  <div class="flex gap-2">
                    <el-button type="success" size="small" @click="handlePriceAction(row.id, 'approve')">{{ t('admin.approve') }}</el-button>
                    <el-button type="danger" size="small" @click="handlePriceAction(row.id, 'reject')">{{ t('admin.reject') }}</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <!-- Pending Providers Tab -->
        <el-tab-pane :label="t('admin.pending_providers')" name="providers">
          <div class="space-y-3">
            <div class="section-header">
              <div>
                <h3 class="text-xl font-semibold text-secondary-900">{{ t('admin.pending_provider_submissions') }}</h3>
                <p class="muted-subtitle">{{ t('admin.pending_providers') }}</p>
              </div>
              <el-badge :value="pendingProviders.length" type="warning" />
            </div>
            
            <div v-if="pendingProviders.length === 0" class="flex items-center justify-between rounded-xl border border-dashed border-gray-200 bg-gray-50 px-4 py-3 text-gray-600">
              <span>{{ t('admin.no_pending_providers') }}</span>
              <el-tag type="info" effect="plain">{{ t('admin.pending_providers') }}</el-tag>
            </div>
            <el-table v-else :data="pendingProviders" v-loading="providersLoading" class="rounded-xl overflow-hidden">
              <el-table-column :label="t('admin.name')">
                <template #default="{ row }">
                  <div class="whitespace-normal break-words">{{ row.name || '-' }}</div>
                </template>
              </el-table-column>
              <el-table-column prop="website" :label="t('keys.website')">
                <template #default="{ row }">
                  <a v-if="row.website" :href="row.website" target="_blank" class="text-primary-600 hover:text-primary-700">{{ row.website }}</a>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column :label="t('admin.base_urls')">
                <template #default="{ row }">
                  <div v-if="row.openai_base_url" class="text-xs">OpenAI: {{ row.openai_base_url }}</div>
                  <div v-if="row.gemini_base_url" class="text-xs">Gemini: {{ row.gemini_base_url }}</div>
                  <div v-if="row.claude_base_url" class="text-xs">Claude: {{ row.claude_base_url }}</div>
                </template>
              </el-table-column>
              <el-table-column :label="t('table.proof')">
                <template #default="{ row }">
                  <span v-if="row.proof_type === 'text'">{{ (row.proof_content || '').substring(0, 50) }}...</span>
                  <a v-else-if="row.proof_type === 'url'" :href="row.proof_content" target="_blank" class="text-primary-600 hover:text-primary-700">{{ t('admin.link') }}</a>
                </template>
              </el-table-column>
              <el-table-column prop="submitter_email" :label="t('admin.submitter')" />
              <el-table-column :label="t('common.actions')" width="180">
                <template #default="{ row }">
                  <div class="flex gap-2">
                    <el-button type="success" size="small" @click="handleProviderAction(row.id, 'approve')">{{ t('admin.approve') }}</el-button>
                    <el-button type="danger" size="small" @click="handleProviderAction(row.id, 'reject')">{{ t('admin.reject') }}</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <!-- Pending Model Requests Tab -->
        <el-tab-pane :label="t('admin.pending_models')" name="models">
          <div class="space-y-3">
            <div class="section-header">
              <div>
                <h3 class="text-xl font-semibold text-secondary-900">{{ t('admin.pending_model_requests') }}</h3>
                <p class="muted-subtitle">{{ t('admin.pending_models') }}</p>
              </div>
              <el-badge :value="pendingModels.length" type="warning" />
            </div>
            
            <div v-if="pendingModels.length === 0" class="flex items-center justify-between rounded-xl border border-dashed border-gray-200 bg-gray-50 px-4 py-3 text-gray-600">
              <span>{{ t('admin.no_pending_model_requests') }}</span>
              <el-tag type="info" effect="plain">{{ t('admin.pending_models') }}</el-tag>
            </div>
            <el-table v-else :data="pendingModels" v-loading="modelsLoading" class="rounded-xl overflow-hidden">
              <el-table-column :label="t('admin.requested_name')">
                <template #default="{ row }">
                  <div class="whitespace-normal break-words">{{ row.requested_name || '-' }}</div>
                </template>
              </el-table-column>
              <el-table-column :label="t('admin.vendor')">
                <template #default="{ row }">
                  <div class="whitespace-normal break-words">{{ row.vendor || '-' }}</div>
                </template>
              </el-table-column>
              <el-table-column prop="requester_email" :label="t('admin.requester')" />
              <el-table-column prop="created_at" :label="t('admin.submitted')" />
              <el-table-column :label="t('common.actions')" width="180">
                <template #default="{ row }">
                  <div class="flex gap-2">
                    <el-button type="success" size="small" @click="handleModelAction(row.id, 'approve')">{{ t('admin.approve') }}</el-button>
                    <el-button type="danger" size="small" @click="handleModelAction(row.id, 'reject')">{{ t('admin.reject') }}</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <!-- Standard Models Management Tab -->
        <el-tab-pane :label="t('admin.manage_models')" name="manage-models">
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="space-y-4">
              <div class="panel p-5">
                <div class="section-header">
                  <div>
                    <p class="section-kicker mb-1">{{ t('admin.manage_models') }}</p>
                    <h3 class="text-xl font-semibold text-secondary-900">{{ t('admin.add_new_model') }}</h3>
                  </div>
                  <el-tag type="success" effect="plain">{{ t('admin.is_featured') }}</el-tag>
                </div>
                <el-form label-position="top" @submit.prevent>
                  <el-form-item :label="t('admin.name')">
                    <el-input v-model="newModel.name" :placeholder="t('admin.model_name_placeholder')" />
                  </el-form-item>
                  <el-form-item :label="t('admin.vendor')">
                    <el-input v-model="newModel.vendor" :placeholder="t('admin.vendor_placeholder')" />
                  </el-form-item>
                  <el-form-item :label="t('admin.official_currency')">
                    <el-select v-model="newModel.official_currency" filterable :loading="currenciesLoading">
                      <el-option v-for="opt in currencyOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                    </el-select>
                  </el-form-item>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <el-form-item :label="t('admin.official_input_price')">
                      <el-input v-model="newModel.official_input_price" type="number" />
                    </el-form-item>
                    <el-form-item :label="t('admin.official_output_price')">
                      <el-input v-model="newModel.official_output_price" type="number" />
                    </el-form-item>
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <el-form-item :label="t('admin.is_featured')">
                      <el-switch v-model="newModel.is_featured" />
                    </el-form-item>
                    <el-form-item :label="t('admin.rank_hint')">
                      <el-input v-model="newModel.rank_hint" type="number" />
                    </el-form-item>
                  </div>
                  <el-alert type="info" :closable="false" class="mb-2">{{ t('admin.featured_hint') }}</el-alert>
                  <div class="flex gap-2">
                    <el-button type="primary" :loading="modelSaving" :disabled="!newModel.name" @click="createModel">{{ t('admin.add') }}</el-button>
                    <el-button @click="resetNewModel">{{ t('common.cancel') }}</el-button>
                  </div>
                </el-form>
              </div>

              <div class="panel p-5">
                <div class="section-header">
                  <div>
                    <p class="section-kicker mb-1">{{ t('admin.manage_models') }}</p>
                    <h3 class="text-lg font-semibold text-secondary-900">{{ t('admin.bulk_import_models') }}</h3>
                    <p class="muted-subtitle">{{ t('admin.bulk_import_hint') }}</p>
                    <el-tag effect="plain" class="whitespace-normal break-words" style="word-break: break-word; white-space: normal;">{{ t('admin.bulk_import_format') }}</el-tag>
                  </div>
                </div>
                <el-input
                  v-model="bulkText"
                  type="textarea"
                  :autosize="{ minRows: 6, maxRows: 20 }"
                  :placeholder="t('admin.bulk_import_placeholder')"
                />
                <div class="flex flex-wrap gap-2 justify-end">
                  <el-button @click="bulkText = ''">{{ t('common.cancel') }}</el-button>
                  <el-button type="primary" :loading="bulkImporting" @click="bulkImportModels">
                    {{ t('admin.import_now') }}
                  </el-button>
                </div>
              </div>
            </div>
            
            <div class="panel p-5 lg:col-span-2">
              <div class="section-header">
                <div>
                  <p class="section-kicker mb-1">{{ t('admin.manage_models') }}</p>
                  <h3 class="text-xl font-semibold text-secondary-900">{{ t('admin.all_standard_models') }}</h3>
                </div>
                <div class="flex items-center gap-2 flex-wrap">
                  <el-tag effect="plain">{{ t('admin.rank_hint') }}</el-tag>
                  <el-tag type="info" effect="plain">{{ t('admin.selected_count', { count: selectedCount }) }}</el-tag>
                  <el-button
                    type="danger"
                    plain
                    :disabled="!selectedCount"
                    :loading="bulkDeleteLoading"
                    @click="deleteSelectedModels"
                  >
                    {{ t('admin.delete_selected') }}
                  </el-button>
                </div>
              </div>
              <el-table
                :data="models"
                height="420"
                v-loading="modelListLoading"
                class="rounded-xl overflow-hidden"
                @selection-change="selectionChanged"
                :row-key="(row: Model) => row.id"
              >
                <el-table-column type="selection" width="50" />
                <el-table-column :label="t('admin.name')" min-width="140">
                  <template #default="{ row }">
                    <div class="whitespace-normal break-words">{{ row.name }}</div>
                  </template>
                </el-table-column>
                <el-table-column :label="t('admin.vendor')" min-width="120">
                  <template #default="{ row }">
                    <div class="whitespace-normal break-words">{{ row.vendor || '-' }}</div>
                  </template>
                </el-table-column>
                <el-table-column :label="t('home.official_price')" min-width="180">
                  <template #default="{ row }">
                    <div class="text-xs leading-5 whitespace-normal break-words">
                      <div v-if="row.official_input_price !== null && row.official_input_price !== undefined">
                        {{ t('table.input') }}: {{ row.official_input_price }} {{ row.official_currency }}
                      </div>
                      <div v-if="row.official_output_price !== null && row.official_output_price !== undefined">
                        {{ t('table.output') }}: {{ row.official_output_price }} {{ row.official_currency }}
                      </div>
                      <div v-if="row.official_input_price === null && row.official_output_price === null" class="text-gray-400">{{ t('home.no_data') }}</div>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column :label="t('admin.is_featured')" width="120" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.is_featured" type="success">{{ t('admin.is_featured') }}</el-tag>
                    <span v-else class="text-gray-400">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="rank_hint" :label="t('admin.rank_hint')" width="120">
                  <template #default="{ row }">
                    {{ row.rank_hint ?? '-' }}
                  </template>
                </el-table-column>
                <el-table-column :label="t('admin.actions')" width="170" fixed="right">
                  <template #default="{ row }">
                    <div class="flex gap-2">
                      <el-button size="small" @click="openEditModel(row)">{{ t('common.edit') }}</el-button>
                      <el-button size="small" type="danger" @click="deleteModel(row.id)">{{ t('common.delete') }}</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>

          <el-dialog v-model="editDialogVisible" :title="t('admin.edit_model')" width="520px">
            <el-form label-position="top" v-if="editingModel">
              <el-form-item :label="t('admin.name')">
                <el-input v-model="editingModel.name" />
              </el-form-item>
              <el-form-item :label="t('admin.vendor')">
                <el-input v-model="editingModel.vendor" />
              </el-form-item>
              <el-form-item :label="t('admin.official_currency')">
                <el-select v-model="editingModel.official_currency" filterable :loading="currenciesLoading">
                  <el-option v-for="opt in currencyOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
              </el-form-item>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <el-form-item :label="t('admin.official_input_price')">
                  <el-input v-model="editingModel.official_input_price" type="number" />
                </el-form-item>
                <el-form-item :label="t('admin.official_output_price')">
                  <el-input v-model="editingModel.official_output_price" type="number" />
                </el-form-item>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <el-form-item :label="t('admin.is_featured')">
                  <el-switch v-model="editingModel.is_featured" />
                </el-form-item>
                <el-form-item :label="t('admin.rank_hint')">
                  <el-input v-model="editingModel.rank_hint" type="number" />
                </el-form-item>
              </div>
            </el-form>
            <template #footer>
              <el-button @click="editDialogVisible = false">{{ t('common.cancel') }}</el-button>
              <el-button type="primary" :loading="editSaving" @click="saveModelEdit">{{ t('admin.update') }}</el-button>
            </template>
          </el-dialog>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>
