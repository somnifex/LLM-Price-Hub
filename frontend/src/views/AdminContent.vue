<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
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

// Active tab
const activeTab = ref('prices')

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
    const res = await api.get('/admin/models/pending')
    pendingModels.value = res.data
  } catch (e) {
    ElMessage.error(t('admin.failed_fetch_models'))
  } finally {
    modelsLoading.value = false
  }
}

const fetchModels = async () => {
  try {
    const res = await api.get('/models')
    models.value = res.data
  } catch {
    // Silent fail
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
    await api.post(`/admin/models/${id}/${action}`)
    ElMessage.success(action === 'approve' ? t('admin.model_approved') : t('admin.model_rejected'))
    fetchPendingModels()
    fetchModels()
  } catch (e) {
    ElMessage.error(t('admin.action_failed'))
  }
}

// Model Management
const newModel = ref({ name: '', vendor: '' })
const createModel = async () => {
  if(!newModel.value.name) return
  try {
    await api.post('/models', newModel.value)
    ElMessage.success(t('admin.model_created'))
    newModel.value = { name: '', vendor: '' }
    fetchModels()
  } catch (e) {
    ElMessage.error(t('admin.failed_create_model'))
  }
}

onMounted(() => {
  fetchPendingPrices()
  fetchPendingProviders()
  fetchPendingModels()
  fetchModels()
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
                <a v-else-if="row.proof_type === 'url'" :href="row.proof_content" target="_blank" class="text-blue-500">{{ t('admin.link') }}</a>
                <a v-else-if="row.proof_img_path" :href="'/' + row.proof_img_path" target="_blank" class="text-blue-500">{{ t('admin.image') }}</a>
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
                <a v-if="row.website" :href="row.website" target="_blank" class="text-blue-500">{{ row.website }}</a>
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
                <a v-else-if="row.proof_type === 'url'" :href="row.proof_content" target="_blank" class="text-blue-500">{{ t('admin.link') }}</a>
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
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <el-card>
            <template #header>{{ t('admin.add_new_model') }}</template>
            <div class="flex gap-2">
              <el-input v-model="newModel.name" :placeholder="t('admin.model_name_placeholder')" />
              <el-input v-model="newModel.vendor" :placeholder="t('admin.vendor_placeholder')" />
              <el-button type="primary" @click="createModel">{{ t('admin.add') }}</el-button>
            </div>
          </el-card>
          
          <el-card>
            <template #header>{{ t('admin.all_standard_models') }}</template>
            <el-table :data="models" height="300">
              <el-table-column prop="name" :label="t('admin.name')" />
              <el-table-column prop="vendor" :label="t('admin.vendor')" />
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
