<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Pending data
const pendingPrices = ref([])
const pendingProviders = ref([])
const pendingModels = ref([])
const models = ref([])

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
  <div>
    <el-tabs v-model="activeTab" type="card">
      <!-- Pending Prices Tab -->
      <el-tab-pane :label="t('admin.pending_prices')" name="prices">
        <el-card>
          <template #header>
            <div class="flex justify-between items-center">
              <span>{{ t('admin.pending_price_submissions') }}</span>
              <el-badge :value="pendingPrices.length" type="warning" />
            </div>
          </template>
          
          <div v-if="pendingPrices.length === 0" class="text-gray-500 py-4">{{ t('admin.no_pending_submissions') }}</div>
          <el-table v-else :data="pendingPrices" v-loading="pricesLoading">
            <el-table-column prop="provider_name" :label="t('table.provider')" />
            <el-table-column prop="model_name" :label="t('admin.standard_model')" />
            <el-table-column prop="provider_model_name" :label="t('admin.provider_model_name')" />
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
                <el-button type="success" size="small" @click="handlePriceAction(row.id, 'approve')">{{ t('admin.approve') }}</el-button>
                <el-button type="danger" size="small" @click="handlePriceAction(row.id, 'reject')">{{ t('admin.reject') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      
      <!-- Pending Providers Tab -->
      <el-tab-pane :label="t('admin.pending_providers')" name="providers">
        <el-card>
          <template #header>
            <div class="flex justify-between items-center">
              <span>{{ t('admin.pending_provider_submissions') }}</span>
              <el-badge :value="pendingProviders.length" type="warning" />
            </div>
          </template>
          
          <div v-if="pendingProviders.length === 0" class="text-gray-500 py-4">{{ t('admin.no_pending_providers') }}</div>
          <el-table v-else :data="pendingProviders" v-loading="providersLoading">
            <el-table-column prop="name" :label="t('admin.name')" />
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
                <el-button type="success" size="small" @click="handleProviderAction(row.id, 'approve')">{{ t('admin.approve') }}</el-button>
                <el-button type="danger" size="small" @click="handleProviderAction(row.id, 'reject')">{{ t('admin.reject') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      
      <!-- Pending Model Requests Tab -->
      <el-tab-pane :label="t('admin.pending_models')" name="models">
        <el-card>
          <template #header>
            <div class="flex justify-between items-center">
              <span>{{ t('admin.pending_model_requests') }}</span>
              <el-badge :value="pendingModels.length" type="warning" />
            </div>
          </template>
          
          <div v-if="pendingModels.length === 0" class="text-gray-500 py-4">{{ t('admin.no_pending_model_requests') }}</div>
          <el-table v-else :data="pendingModels" v-loading="modelsLoading">
            <el-table-column prop="requested_name" :label="t('admin.requested_name')" />
            <el-table-column prop="vendor" :label="t('admin.vendor')" />
            <el-table-column prop="requester_email" :label="t('admin.requester')" />
            <el-table-column prop="created_at" :label="t('admin.submitted')" />
            <el-table-column :label="t('common.actions')" width="180">
              <template #default="{ row }">
                <el-button type="success" size="small" @click="handleModelAction(row.id, 'approve')">{{ t('admin.approve') }}</el-button>
                <el-button type="danger" size="small" @click="handleModelAction(row.id, 'reject')">{{ t('admin.reject') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      
      <!-- Standard Models Management Tab -->
      <el-tab-pane :label="t('admin.manage_models')" name="manage-models">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <el-card class="lg:col-span-1">
            <template #header>{{ t('admin.add_new_model') }}</template>
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
          </el-card>
          
          <el-card class="lg:col-span-2">
            <template #header>{{ t('admin.all_standard_models') }}</template>
            <el-table :data="models" height="420" v-loading="modelListLoading">
              <el-table-column prop="name" :label="t('admin.name')" min-width="140" />
              <el-table-column prop="vendor" :label="t('admin.vendor')" min-width="120" />
              <el-table-column :label="t('home.official_price')" min-width="180">
                <template #default="{ row }">
                  <div class="text-xs leading-5">
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
          </el-card>
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
</template>
