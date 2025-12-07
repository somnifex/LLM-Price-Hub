<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()

// Data
const models = ref<Array<{id: number, name: string, vendor?: string}>>([])
const providers = ref<Array<{id: number, name: string, status?: string}>>([])
const loading = ref(false)

// Form state
const providerMode = ref<'existing' | 'new'>('existing')
const modelMode = ref<'existing' | 'new'>('existing')

const form = ref({
  // Provider
  provider_id: null as number | null,
  provider_name: '',
  provider_website: '',
  openai_base_url: '',
  gemini_base_url: '',
  claude_base_url: '',
  submit_provider_for_review: false,
  provider_proof_type: 'text',
  provider_proof_content: '',
  
  // Model
  standard_model_id: null as number | null,
  new_model_name: '',
  new_model_vendor: '',
  provider_model_name: '',
  
  // Price
  price_in: 0,
  price_out: 0,
  currency: 'USD',
  
  // Proof
  proof_type: 'text',
  proof_content: ''
})

const file = ref<File | null>(null)

const handleFileChange = (uploadFile: any) => {
  file.value = uploadFile.raw
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
  // Validation
  if (providerMode.value === 'existing' && !form.value.provider_id) {
    ElMessage.error(t('submit.select_provider_error'))
    return
  }
  if (providerMode.value === 'new' && !form.value.provider_name) {
    ElMessage.error(t('submit.enter_provider_name'))
    return
  }
  if (modelMode.value === 'existing' && !form.value.standard_model_id) {
    ElMessage.error(t('submit.select_model_error'))
    return
  }
  if (modelMode.value === 'new' && !form.value.new_model_name) {
    ElMessage.error(t('submit.enter_model_name'))
    return
  }
  if (!form.value.proof_type || !form.value.proof_content) {
    if (form.value.proof_type !== 'image' || !file.value) {
      ElMessage.error(t('submit.proof_required'))
      return
    }
  }

  loading.value = true
  const formData = new FormData()
  
  // Provider
  if (providerMode.value === 'existing') {
    formData.append('provider_id', String(form.value.provider_id))
  } else {
    formData.append('provider_name', form.value.provider_name)
    formData.append('provider_website', form.value.provider_website)
    formData.append('openai_base_url', form.value.openai_base_url)
    formData.append('gemini_base_url', form.value.gemini_base_url)
    formData.append('claude_base_url', form.value.claude_base_url)
    formData.append('submit_provider_for_review', String(form.value.submit_provider_for_review))
    if (form.value.submit_provider_for_review) {
      formData.append('provider_proof_type', form.value.provider_proof_type)
      formData.append('provider_proof_content', form.value.provider_proof_content)
    }
  }
  
  // Model
  if (modelMode.value === 'existing') {
    formData.append('standard_model_id', String(form.value.standard_model_id))
  } else {
    formData.append('new_model_name', form.value.new_model_name)
    formData.append('new_model_vendor', form.value.new_model_vendor)
  }
  formData.append('provider_model_name', form.value.provider_model_name)
  
  // Price
  formData.append('price_in', form.value.price_in.toString())
  formData.append('price_out', form.value.price_out.toString())
  formData.append('currency', form.value.currency)
  
  // Proof
  formData.append('proof_type', form.value.proof_type)
  if (form.value.proof_type === 'image' && file.value) {
    formData.append('file', file.value)
    formData.append('proof_content', '')
  } else {
    formData.append('proof_content', form.value.proof_content)
  }

  try {
    await api.post('/prices/submit', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success(t('submit.success'))
    router.push('/')
  } catch (e: any) {
    if (e.response?.status === 202) {
      // Model request submitted
      let msg = e.response.data.detail
      if (Array.isArray(msg)) {
        msg = msg.map((err: any) => err.msg).join(', ')
      }
      ElMessage.warning(msg)
    } else {
      let msg = e.response?.data?.detail
      if (Array.isArray(msg)) {
        msg = msg.map((err: any) => err.msg).join(', ')
      }
      ElMessage.error(msg || t('submit.failed'))
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchModels()
  fetchProviders()
})
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <h2 class="text-3xl font-bold mb-6">{{ t('submit.title') }}</h2>
    <div class="bg-white p-6 rounded-lg shadow border border-gray-100">
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
              <el-select v-model="form.provider_id" class="w-full" filterable>
                <el-option v-for="p in providers" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </template>
          
          <template v-else>
            <el-form-item :label="t('submit.provider_name')">
              <el-input v-model="form.provider_name" :placeholder="t('submit.provider_name_placeholder')" />
            </el-form-item>
            <el-form-item :label="t('submit.provider_website')">
              <el-input v-model="form.provider_website" placeholder="https://example.com" />
            </el-form-item>
            
            <el-collapse class="mb-4">
              <el-collapse-item :title="t('submit.api_base_urls')">
                <el-form-item label="OpenAI Base URL">
                  <el-input v-model="form.openai_base_url" placeholder="https://api.openai.com/v1" />
                </el-form-item>
                <el-form-item label="Gemini Base URL">
                  <el-input v-model="form.gemini_base_url" />
                </el-form-item>
                <el-form-item label="Claude Base URL">
                  <el-input v-model="form.claude_base_url" />
                </el-form-item>
              </el-collapse-item>
            </el-collapse>
            
            <el-form-item>
              <el-switch v-model="form.submit_provider_for_review" :active-text="t('submit.submit_provider_public')" />
            </el-form-item>
            
            <template v-if="form.submit_provider_for_review">
              <el-form-item :label="t('submit.provider_proof')">
                <el-radio-group v-model="form.provider_proof_type">
                  <el-radio value="text">{{ t('submit.proof_text') }}</el-radio>
                  <el-radio value="url">{{ t('submit.proof_url') }}</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item>
                <el-input v-model="form.provider_proof_content" 
                  :type="form.provider_proof_type === 'text' ? 'textarea' : 'text'"
                  :placeholder="form.provider_proof_type === 'url' ? 'https://docs.example.com/pricing' : t('submit.proof_description')" />
              </el-form-item>
            </template>
          </template>
        </div>
        
        <!-- Model Section -->
        <div class="mb-6">
          <h3 class="text-lg font-semibold mb-4 border-b pb-2">{{ t('submit.model_section') }}</h3>
          
          <el-radio-group v-model="modelMode" class="mb-4">
            <el-radio value="existing">{{ t('submit.use_existing_model') }}</el-radio>
            <el-radio value="new">{{ t('submit.request_new_model') }}</el-radio>
          </el-radio-group>
          
          <template v-if="modelMode === 'existing'">
            <el-form-item :label="t('submit.standard_model')">
              <el-select v-model="form.standard_model_id" :placeholder="t('submit.select_model')" class="w-full" filterable>
                <el-option v-for="m in models" :key="m.id" :label="`${m.name}${m.vendor ? ' (' + m.vendor + ')' : ''}`" :value="m.id" />
              </el-select>
            </el-form-item>
          </template>
          
          <template v-else>
            <el-form-item :label="t('submit.new_model_name')">
              <el-input v-model="form.new_model_name" placeholder="e.g. claude-3.5-sonnet" />
            </el-form-item>
            <el-form-item :label="t('submit.model_vendor')">
              <el-input v-model="form.new_model_vendor" placeholder="e.g. Anthropic" />
            </el-form-item>
            <el-alert type="info" :closable="false" class="mb-4">
              {{ t('submit.new_model_notice') }}
            </el-alert>
          </template>
          
          <el-form-item :label="t('submit.provider_model_name')">
            <el-input v-model="form.provider_model_name" :placeholder="t('submit.provider_model_name_placeholder')" />
            <span class="text-xs text-gray-500">{{ t('submit.provider_model_name_hint') }}</span>
          </el-form-item>
        </div>
        
        <!-- Price Section -->
        <div class="mb-6">
          <h3 class="text-lg font-semibold mb-4 border-b pb-2">{{ t('submit.price_section') }}</h3>
          
          <div class="grid grid-cols-2 gap-4">
            <el-form-item :label="t('submit.input_price')">
              <el-input-number v-model="form.price_in" :precision="6" :step="0.01" class="w-full" />
            </el-form-item>
            <el-form-item :label="t('submit.output_price')">
              <el-input-number v-model="form.price_out" :precision="6" :step="0.01" class="w-full" />
            </el-form-item>
          </div>

          <el-form-item :label="t('submit.currency')">
            <el-select v-model="form.currency">
              <el-option label="USD" value="USD" />
              <el-option label="CNY" value="CNY" />
              <el-option label="EUR" value="EUR" />
            </el-select>
          </el-form-item>
        </div>
        
        <!-- Proof Section -->
        <div class="mb-6">
          <h3 class="text-lg font-semibold mb-4 border-b pb-2">{{ t('submit.proof_section') }}</h3>
          
          <el-form-item :label="t('submit.proof_type')">
            <el-radio-group v-model="form.proof_type">
              <el-radio value="text">{{ t('submit.proof_text') }}</el-radio>
              <el-radio value="url">{{ t('submit.proof_url') }}</el-radio>
              <el-radio value="image">{{ t('submit.proof_image') }}</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item v-if="form.proof_type === 'text'">
            <el-input v-model="form.proof_content" type="textarea" :rows="3" :placeholder="t('submit.proof_description')" />
          </el-form-item>
          
          <el-form-item v-else-if="form.proof_type === 'url'">
            <el-input v-model="form.proof_content" placeholder="https://docs.example.com/pricing" />
          </el-form-item>
          
          <el-form-item v-else>
            <el-upload
              class="upload-demo"
              action="#"
              :auto-upload="false"
              :limit="1"
              :on-change="handleFileChange"
            >
              <el-button type="primary">{{ t('submit.select_image') }}</el-button>
            </el-upload>
          </el-form-item>
        </div>

        <el-button type="primary" size="large" class="w-full" @click="submit" :loading="loading">
          {{ t('submit.submit_btn') }}
        </el-button>
      </el-form>
    </div>
  </div>
</template>
