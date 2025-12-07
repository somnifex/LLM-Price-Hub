<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { CopyDocument, View, Hide } from '@element-plus/icons-vue'
import api from '@/api'
import { encrypt, decrypt, generateSalt, verifyPassword } from '@/utils/e2ee'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
// @ts-ignore
import QRCode from 'qrcode'

const { t } = useI18n()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const activeTab = ref('general')

// General Settings State
const preferredCurrencies = ref<string[]>([])
const defaultCurrency = ref('USD')
const settingsLoading = ref(false)

// TOTP State
const totpEnabled = ref(false)
const totpSecret = ref('')
const totpUrl = ref('')
const totpQr = ref('')
const totpBackupCodes = ref<string[]>([])
const totpCode = ref('')
const showTotpDialog = ref(false)
const showDisableTotp = ref(false)
const totpLoading = ref(false)

// E2EE State
const e2eeEnabled = ref(false)
const e2eeSalt = ref('')
const e2eeVerification = ref('')
const password = ref('')
const showPasswordPrompt = ref(false)
const showE2EESetup = ref(false)
const newPassword = ref('')
const confirmPassword = ref('')

// API Keys State
const apiKeys = ref<any[]>([])
const providers = ref<any[]>([])
const showAddKeyDialog = ref(false)
const visibleKeyIds = ref<Set<number>>(new Set()) // Track which keys are visible
const newKey = ref({
  provider_id: null as number | null,
  api_key: '',
  note: ''
})

// Providers State
const userProviders = ref<any[]>([])
const showAddProviderDialog = ref(false)
const newProvider = ref({
  name: '',
  website: '',
  openai_base_url: '',
  gemini_base_url: '',
  claude_base_url: '',
  submit_for_review: false,
  proof_type: 'text',
  proof_content: ''
})
const editingProvider = ref<any>(null)
const showEditProviderDialog = ref(false)

const loading = ref(false)
const keysLoading = ref(false)
const providersLoading = ref(false)

// General Settings Functions
async function loadGeneralSettings() {
  await settingsStore.fetchCurrencies()
  await settingsStore.fetchUserSettings()
  preferredCurrencies.value = settingsStore.userSettings.preferred_currencies
  defaultCurrency.value = settingsStore.userSettings.default_currency
}

async function saveGeneralSettings() {
  settingsLoading.value = true
  try {
    await settingsStore.updateUserSettings(preferredCurrencies.value, defaultCurrency.value)
    ElMessage.success(t('settings.saved'))
  } catch {
    ElMessage.error(t('settings.save_failed'))
  } finally {
    settingsLoading.value = false
  }
}

// Utility: Copy to clipboard
async function copyToClipboard(text: string, label: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(t('keys.copied', { item: label }))
  } catch {
    ElMessage.error(t('keys.copy_failed'))
  }
}

// Key visibility
function isKeyVisible(keyId: number): boolean {
  return visibleKeyIds.value.has(keyId)
}

async function toggleKeyVisibility(key: any) {
  if (isKeyVisible(key.id)) {
    visibleKeyIds.value.delete(key.id)
    return
  }
  
  // If E2EE enabled and no password, prompt for it
  if (e2eeEnabled.value && !password.value) {
    showPasswordPrompt.value = true
    return
  }
  
  visibleKeyIds.value.add(key.id)
}

function getDisplayKey(key: any): string {
  if (!isKeyVisible(key.id)) {
    return '••••••••••••••••'
  }
  
  if (key.is_encrypted && password.value && e2eeSalt.value) {
    try {
      return decrypt(key.api_key, password.value, e2eeSalt.value)
    } catch {
      return '[Decryption Failed]'
    }
  }
  return key.api_key
}

function getActualKey(key: any): string {
  if (key.is_encrypted && password.value && e2eeSalt.value) {
    try {
      return decrypt(key.api_key, password.value, e2eeSalt.value)
    } catch {
      return ''
    }
  }
  return key.api_key
}

// E2EE Functions
async function loadSettings() {
  try {
    const res = await api.get('/user/settings')
    e2eeEnabled.value = res.data.e2ee_enabled
    e2eeSalt.value = res.data.e2ee_salt || ''
    e2eeVerification.value = res.data.e2ee_verification || ''
  } catch {
    // Silent fail - settings will use defaults
  }
}

async function loadTotpStatus() {
  try {
    const res = await api.get('/auth/totp/status')
    totpEnabled.value = res.data.enabled
    totpBackupCodes.value = []
  } catch {
    totpEnabled.value = false
  }
}

async function startTotpSetup() {
  totpLoading.value = true
  try {
    const res = await api.post('/auth/totp/initiate')
    totpSecret.value = res.data.secret
    totpUrl.value = res.data.otpauth_url
    totpQr.value = await QRCode.toDataURL(res.data.otpauth_url)
    totpBackupCodes.value = []
    totpCode.value = ''
    showTotpDialog.value = true
  } catch (error) {
    ElMessage.error(t('keys.failed_to_load_totp'))
  } finally {
    totpLoading.value = false
  }
}

async function confirmTotpSetup() {
  if (!totpCode.value) {
    ElMessage.error(t('keys.enter_totp_code'))
    return
  }
  totpLoading.value = true
  try {
    const res = await api.post('/auth/totp/activate', { code: totpCode.value })
    totpEnabled.value = true
    totpBackupCodes.value = res.data.backup_codes || []
    totpCode.value = ''
    ElMessage.success(t('keys.totp_enabled'))
  } catch (error) {
    ElMessage.error(t('keys.invalid_totp'))
  } finally {
    totpLoading.value = false
  }
}

async function disableTotp() {
  if (!totpEnabled.value) return
  if (!totpCode.value) {
    ElMessage.error(t('keys.enter_totp_code'))
    return
  }
  totpLoading.value = true
  try {
    await api.post('/auth/totp/disable', { code: totpCode.value })
    totpEnabled.value = false
    totpSecret.value = ''
    totpUrl.value = ''
    totpBackupCodes.value = []
    showDisableTotp.value = false
    totpCode.value = ''
    ElMessage.success(t('keys.totp_disabled'))
  } catch (error) {
    ElMessage.error(t('keys.invalid_totp'))
  } finally {
    totpLoading.value = false
  }
}

function verifyE2EEPassword() {
  if (verifyPassword(password.value, e2eeSalt.value, e2eeVerification.value)) {
    showPasswordPrompt.value = false
    ElMessage.success(t('keys.password_verified'))
  } else {
    ElMessage.error(t('keys.invalid_password'))
  }
}

async function setupE2EE() {
  if (newPassword.value !== confirmPassword.value) {
    ElMessage.error(t('keys.passwords_do_not_match'))
    return
  }
  
  if (newPassword.value.length < 6) {
    ElMessage.error(t('keys.password_too_short'))
    return
  }
  
  loading.value = true
  try {
    const salt = generateSalt()
    const verification = encrypt('VERIFIED', newPassword.value, salt)
    
    await api.post('/user/settings/e2ee', { salt, verification })
    
    e2eeEnabled.value = true
    e2eeSalt.value = salt
    e2eeVerification.value = verification
    password.value = newPassword.value
    showE2EESetup.value = false
    newPassword.value = ''
    confirmPassword.value = ''
    
    ElMessage.success(t('keys.e2ee_enabled'))
  } catch (error) {
    ElMessage.error(t('keys.failed_to_enable_e2ee'))
  } finally {
    loading.value = false
  }
}

async function disableE2EE() {
  try {
    await ElMessageBox.confirm(t('keys.disable_e2ee_warning'), t('common.warning'), { type: 'warning' })
    await api.delete('/user/settings/e2ee')
    e2eeEnabled.value = false
    e2eeSalt.value = ''
    e2eeVerification.value = ''
    password.value = ''
    ElMessage.success(t('keys.e2ee_disabled'))
  } catch {}
}

// API Keys Functions
async function loadAPIKeys() {
  keysLoading.value = true
  try {
    const res = await api.get('/user/keys')
    apiKeys.value = res.data
  } catch (error) {
    ElMessage.error(t('keys.failed_to_load_keys'))
  } finally {
    keysLoading.value = false
  }
}

async function addAPIKey() {
  if (!newKey.value.provider_id || !newKey.value.api_key) {
    ElMessage.error(t('keys.please_fill_all_fields'))
    return
  }
  
  loading.value = true
  try {
    let apiKeyToSend = newKey.value.api_key
    let isEncrypted = false
    
    if (e2eeEnabled.value && password.value && e2eeSalt.value) {
      apiKeyToSend = encrypt(newKey.value.api_key, password.value, e2eeSalt.value)
      isEncrypted = true
    }
    
    await api.post('/user/keys', {
      provider_id: newKey.value.provider_id,
      api_key: apiKeyToSend,
      is_encrypted: isEncrypted,
      note: newKey.value.note
    })
    
    showAddKeyDialog.value = false
    newKey.value = { provider_id: null, api_key: '', note: '' }
    await loadAPIKeys()
    
    ElMessage.success(t('keys.key_added'))
  } catch (error: any) {
    let msg = error.response?.data?.detail
    if (Array.isArray(msg)) {
      msg = msg.map((err: any) => err.msg).join(', ')
    }
    ElMessage.error(msg || t('keys.failed_to_add_key'))
  } finally {
    loading.value = false
  }
}

async function deleteAPIKey(keyId: number) {
  try {
    await ElMessageBox.confirm(t('keys.confirm_delete_key'), t('common.warning'), { type: 'warning' })
    await api.delete(`/user/keys/${keyId}`)
    await loadAPIKeys()
    ElMessage.success(t('keys.key_deleted'))
  } catch {}
}

// Providers Functions
async function loadProviders() {
  providersLoading.value = true
  try {
    const [publicRes, privateRes] = await Promise.all([
      api.get('/config/providers'),
      api.get('/user/providers')
    ])
    
    providers.value = publicRes.data
    userProviders.value = privateRes.data
  } catch (error) {
    ElMessage.error(t('keys.failed_to_load_providers'))
  } finally {
    providersLoading.value = false
  }
}

async function addProvider() {
  if (!newProvider.value.name) {
    ElMessage.error(t('keys.please_enter_provider_name'))
    return
  }
  
  if (newProvider.value.submit_for_review && !newProvider.value.proof_content) {
    ElMessage.error(t('keys.proof_required'))
    return
  }
  
  loading.value = true
  try {
    await api.post('/user/providers', newProvider.value)
    showAddProviderDialog.value = false
    newProvider.value = {
      name: '', website: '', openai_base_url: '', gemini_base_url: '', claude_base_url: '',
      submit_for_review: false, proof_type: 'text', proof_content: ''
    }
    await loadProviders()
    
    ElMessage.success(t('keys.provider_added'))
  } catch (error) {
    ElMessage.error(t('keys.failed_to_add_provider'))
  } finally {
    loading.value = false
  }
}

async function updateProvider() {
  if (!editingProvider.value) return
  
  loading.value = true
  try {
    await api.put(`/user/providers/${editingProvider.value.id}`, {
      name: editingProvider.value.name,
      website: editingProvider.value.website,
      openai_base_url: editingProvider.value.openai_base_url,
      gemini_base_url: editingProvider.value.gemini_base_url,
      claude_base_url: editingProvider.value.claude_base_url
    })
    
    editingProvider.value = null
    showEditProviderDialog.value = false
    await loadProviders()
    
    ElMessage.success(t('keys.provider_updated'))
  } catch (error) {
    ElMessage.error(t('keys.failed_to_update_provider'))
  } finally {
    loading.value = false
  }
}

async function deleteProvider(providerId: number) {
  try {
    await ElMessageBox.confirm(t('keys.confirm_delete_provider'), t('common.warning'), { type: 'warning' })
    await api.delete(`/user/providers/${providerId}`)
    await loadProviders()
    ElMessage.success(t('keys.provider_deleted'))
  } catch (error: any) {
    let msg = error.response?.data?.detail
    if (msg) {
      if (Array.isArray(msg)) {
        msg = msg.map((err: any) => err.msg).join(', ')
      }
      ElMessage.error(msg)
    }
  }
}

function getAllProviders() {
  return [...providers.value, ...userProviders.value]
}

function getStatusTag(status: string) {
  const map: Record<string, string> = {
    private: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

onMounted(async () => {
  await loadGeneralSettings()
  await loadTotpStatus()
  await loadSettings()
  await loadProviders()
  await loadAPIKeys()
})
</script>

<template>
  <div class="container mx-auto p-6 max-w-6xl">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">{{ t('keys.user_settings') }}</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="$router.push('/admin')">
        {{ t('keys.admin_dashboard') }}
      </el-button>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- General Tab -->
      <el-tab-pane :label="t('settings.general_tab')" name="general">
        <el-card shadow="never">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="text-xl font-bold">{{ t('settings.general_tab') }}</span>
            </div>
          </template>
          
          <div class="space-y-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('settings.preferred_currencies') }}</label>
              <el-select
                v-model="preferredCurrencies"
                multiple
                filterable
                placeholder="Select currencies"
                class="w-full"
              >
                <el-option
                  v-for="item in settingsStore.availableCurrencies"
                  :key="item.code"
                  :label="item.code"
                  :value="item.code"
                />
              </el-select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('settings.default_currency') }}</label>
              <el-select
                v-model="defaultCurrency"
                filterable
                placeholder="Select default currency"
                class="w-full"
              >
                <el-option
                  v-for="code in preferredCurrencies"
                  :key="code"
                  :label="code"
                  :value="code"
                />
              </el-select>
            </div>

            <div class="pt-4">
              <el-button type="primary" :loading="settingsLoading" @click="saveGeneralSettings">
                {{ t('settings.save') }}
              </el-button>
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- Security Tab -->
      <el-tab-pane :label="t('keys.security_tab')" name="security">
        <!-- TOTP Section -->
        <el-card class="mb-6" shadow="never">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="text-xl font-bold">{{ t('keys.totp_title') }}</span>
              <el-tag :type="totpEnabled ? 'success' : 'info'">{{ totpEnabled ? t('keys.enabled') : t('keys.disabled') }}</el-tag>
            </div>
          </template>

          <div v-if="!totpEnabled" class="space-y-3">
            <p class="text-gray-600">{{ t('keys.totp_description') }}</p>
            <el-button type="primary" :loading="totpLoading" @click="startTotpSetup">{{ t('keys.enable_totp') }}</el-button>
          </div>

          <div v-else class="space-y-3">
            <el-alert type="success" :closable="false">{{ t('keys.totp_active') }}</el-alert>
            <el-button type="danger" @click="totpCode = ''; showDisableTotp = true">{{ t('keys.disable_totp') }}</el-button>
          </div>

          <div v-if="totpBackupCodes.length" class="mt-4 bg-gray-50 p-3 rounded">
            <p class="font-semibold mb-2">{{ t('keys.backup_codes') }}</p>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
              <code v-for="code in totpBackupCodes" :key="code" class="block bg-white border px-2 py-1 rounded text-center">{{ code }}</code>
            </div>
            <p class="text-xs text-gray-500 mt-2">{{ t('keys.backup_codes_hint') }}</p>
          </div>
        </el-card>
        
        <!-- E2EE Settings Section -->
        <el-card shadow="never">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="text-xl font-bold">{{ t('keys.encryption_settings') }}</span>
              <el-tag v-if="e2eeEnabled" type="success">{{ t('keys.enabled') }}</el-tag>
              <el-tag v-else type="info">{{ t('keys.disabled') }}</el-tag>
            </div>
          </template>
          
          <div v-if="!e2eeEnabled" class="space-y-4">
            <p>{{ t('keys.e2ee_description') }}</p>
            <el-button type="primary" @click="showE2EESetup = true">
              {{ t('keys.enable_encryption') }}
            </el-button>
          </div>
          
          <div v-else class="space-y-4">
            <el-alert type="success" :closable="false">
              {{ t('keys.e2ee_active') }}
            </el-alert>
            <el-button type="danger" @click="disableE2EE">
              {{ t('keys.disable_encryption') }}
            </el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- API Keys Tab -->
      <el-tab-pane :label="t('keys.api_keys_tab')" name="api_keys">
        <el-card shadow="never">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="text-xl font-bold">{{ t('keys.my_api_keys') }}</span>
              <el-button type="primary" size="small" @click="showAddKeyDialog = true">
                {{ t('keys.add_key') }}
              </el-button>
            </div>
          </template>
          
          <el-table :data="apiKeys" v-loading="keysLoading" stripe>
            <el-table-column prop="provider_name" :label="t('keys.provider')" />
            <el-table-column :label="t('keys.api_key')" min-width="250">
              <template #default="{ row }">
                <div class="flex items-center gap-2">
                  <code class="flex-1 text-sm font-mono">{{ getDisplayKey(row) }}</code>
                  <el-button size="small" :icon="isKeyVisible(row.id) ? Hide : View" circle @click="toggleKeyVisibility(row)" />
                  <el-button size="small" :icon="CopyDocument" circle @click="copyToClipboard(getActualKey(row), 'API Key')" :disabled="!isKeyVisible(row.id) && row.is_encrypted" />
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="note" :label="t('keys.note')" />
            <el-table-column :label="t('keys.status')" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_encrypted" type="success" size="small">
                  {{ t('keys.encrypted') }}
                </el-tag>
                <el-tag v-else type="info" size="small">
                  {{ t('keys.plaintext') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" width="100">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="deleteAPIKey(row.id)">
                  {{ t('common.delete') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- Channels Tab -->
      <el-tab-pane :label="t('keys.channels_tab')" name="channels">
        <el-card shadow="never">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="text-xl font-bold">{{ t('keys.my_providers') }}</span>
              <el-button type="primary" size="small" @click="showAddProviderDialog = true">
                {{ t('keys.add_provider') }}
              </el-button>
            </div>
          </template>
          
          <el-table :data="userProviders" v-loading="providersLoading" stripe>
            <el-table-column prop="name" :label="t('keys.provider_name')" />
            <el-table-column prop="website" :label="t('keys.website')" />
            <el-table-column :label="t('keys.status')">
              <template #default="{ row }">
                <el-tag :type="getStatusTag(row.status)" size="small">
                  {{ t('keys.status_' + row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('keys.base_urls')" min-width="200">
              <template #default="{ row }">
                <div class="space-y-1">
                  <div v-if="row.openai_base_url" class="flex items-center gap-1 text-xs">
                    <span class="text-gray-500">OpenAI:</span>
                    <code class="flex-1 truncate">{{ row.openai_base_url }}</code>
                    <el-button size="small" :icon="CopyDocument" circle @click="copyToClipboard(row.openai_base_url, 'OpenAI URL')" />
                  </div>
                  <div v-if="row.gemini_base_url" class="flex items-center gap-1 text-xs">
                    <span class="text-gray-500">Gemini:</span>
                    <code class="flex-1 truncate">{{ row.gemini_base_url }}</code>
                    <el-button size="small" :icon="CopyDocument" circle @click="copyToClipboard(row.gemini_base_url, 'Gemini URL')" />
                  </div>
                  <div v-if="row.claude_base_url" class="flex items-center gap-1 text-xs">
                    <span class="text-gray-500">Claude:</span>
                    <code class="flex-1 truncate">{{ row.claude_base_url }}</code>
                    <el-button size="small" :icon="CopyDocument" circle @click="copyToClipboard(row.claude_base_url, 'Claude URL')" />
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="editingProvider = { ...row }; showEditProviderDialog = true">
                  {{ t('common.edit') }}
                </el-button>
                <el-button size="small" type="danger" @click="deleteProvider(row.id)">
                  {{ t('common.delete') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- TOTP Setup Dialog -->
    <el-dialog v-model="showTotpDialog" :title="t('keys.enable_totp')" width="520px">
      <div class="space-y-3">
        <p>{{ t('keys.totp_scan_hint') }}</p>
        <el-alert type="info" :closable="false">
          <div class="break-all">{{ totpUrl }}</div>
        </el-alert>
        <div v-if="totpQr" class="flex justify-center">
          <img :src="totpQr" alt="TOTP QR" class="w-40 h-40" />
        </div>
        <el-form @submit.prevent="confirmTotpSetup">
          <el-form-item :label="t('keys.totp_secret')">
            <el-input v-model="totpSecret" readonly />
          </el-form-item>
          <el-form-item :label="t('keys.totp_code')">
            <el-input v-model="totpCode" />
          </el-form-item>
        </el-form>
        <el-alert type="warning" :closable="false">{{ t('keys.backup_code_notice') }}</el-alert>
        <div v-if="totpBackupCodes.length" class="bg-gray-50 border rounded p-3 space-y-2">
          <div class="text-sm font-semibold">{{ t('keys.backup_codes') }}</div>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
            <code v-for="code in totpBackupCodes" :key="code" class="bg-white border rounded px-2 py-1 block text-center font-mono text-sm">{{ code }}</code>
          </div>
          <div class="text-xs text-gray-500">{{ t('keys.backup_codes_hint') }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showTotpDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="totpLoading" @click="confirmTotpSetup">{{ totpBackupCodes.length ? t('common.confirm') : t('keys.enable_totp') }}</el-button>
      </template>
    </el-dialog>

    <!-- Disable TOTP Dialog -->
    <el-dialog v-model="showDisableTotp" :title="t('keys.disable_totp')" width="420px">
      <el-form @submit.prevent="disableTotp">
        <el-form-item :label="t('keys.totp_code')">
          <el-input v-model="totpCode" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDisableTotp = false">{{ t('common.cancel') }}</el-button>
        <el-button type="danger" :loading="totpLoading" @click="disableTotp">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- Password Prompt Dialog -->
    <el-dialog v-model="showPasswordPrompt" :title="t('keys.enter_password')" :close-on-click-modal="false">
      <el-form @submit.prevent="verifyE2EEPassword">
        <el-form-item :label="t('keys.password')">
          <el-input v-model="password" type="password" show-password />
        </el-form-item>
        <el-alert type="warning" :closable="false" class="mb-4">
          {{ t('keys.password_required_to_decrypt') }}
        </el-alert>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="verifyE2EEPassword">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- E2EE Setup Dialog -->
    <el-dialog v-model="showE2EESetup" :title="t('keys.setup_encryption')">
      <el-form @submit.prevent="setupE2EE">
        <el-alert type="warning" :closable="false" class="mb-4">
          <strong>{{ t('keys.password_warning_title') }}</strong><br>
          {{ t('keys.password_warning_message') }}
        </el-alert>
        <el-form-item :label="t('keys.new_password')">
          <el-input v-model="newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('keys.confirm_password')">
          <el-input v-model="confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showE2EESetup = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="setupE2EE" :loading="loading">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- Add API Key Dialog -->
    <el-dialog v-model="showAddKeyDialog" :title="t('keys.add_key')">
      <el-form @submit.prevent="addAPIKey">
        <el-form-item :label="t('keys.provider')">
          <el-select v-model="newKey.provider_id" class="w-full">
            <el-option v-for="provider in getAllProviders()" :key="provider.id" :label="provider.name" :value="provider.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('keys.api_key')">
          <el-input v-model="newKey.api_key" type="textarea" />
        </el-form-item>
        <el-form-item :label="t('keys.note')">
          <el-input v-model="newKey.note" />
        </el-form-item>
        <el-alert v-if="e2eeEnabled" type="info" :closable="false">
          {{ t('keys.key_will_be_encrypted') }}
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="showAddKeyDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="addAPIKey" :loading="loading">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- Add Provider Dialog -->
    <el-dialog v-model="showAddProviderDialog" :title="t('keys.add_provider')" width="600px">
      <el-form @submit.prevent="addProvider" label-width="140px">
        <el-form-item :label="t('keys.provider_name')" required>
          <el-input v-model="newProvider.name" />
        </el-form-item>
        <el-form-item :label="t('keys.website')">
          <el-input v-model="newProvider.website" placeholder="https://example.com" />
        </el-form-item>
        
        <el-divider>{{ t('keys.api_base_urls') }}</el-divider>
        
        <el-form-item label="OpenAI Base URL">
          <el-input v-model="newProvider.openai_base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="Gemini Base URL">
          <el-input v-model="newProvider.gemini_base_url" placeholder="https://generativelanguage.googleapis.com/v1" />
        </el-form-item>
        <el-form-item label="Claude Base URL">
          <el-input v-model="newProvider.claude_base_url" placeholder="https://api.anthropic.com/v1" />
        </el-form-item>
        
        <el-divider>{{ t('keys.submission') }}</el-divider>
        
        <el-form-item :label="t('keys.submit_for_review')">
          <el-switch v-model="newProvider.submit_for_review" />
        </el-form-item>
        
        <template v-if="newProvider.submit_for_review">
          <el-form-item :label="t('keys.proof_type')">
            <el-radio-group v-model="newProvider.proof_type">
              <el-radio value="text">{{ t('keys.proof_text') }}</el-radio>
              <el-radio value="url">{{ t('keys.proof_url') }}</el-radio>
              <el-radio value="image">{{ t('keys.proof_image') }}</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item :label="t('keys.proof_content')">
            <el-input 
              v-model="newProvider.proof_content" 
              :type="newProvider.proof_type === 'text' ? 'textarea' : 'text'"
              :placeholder="newProvider.proof_type === 'url' ? 'https://docs.example.com/pricing' : ''"
            />
          </el-form-item>
        </template>
        
        <el-alert v-if="!newProvider.submit_for_review" type="info" :closable="false">
          {{ t('keys.private_provider_notice') }}
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="showAddProviderDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="addProvider" :loading="loading">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- Edit Provider Dialog -->
    <el-dialog v-model="showEditProviderDialog" :title="t('keys.edit_provider')" width="600px">
      <el-form @submit.prevent="updateProvider" v-if="editingProvider" label-width="140px">
        <el-form-item :label="t('keys.provider_name')">
          <el-input v-model="editingProvider.name" />
        </el-form-item>
        <el-form-item :label="t('keys.website')">
          <el-input v-model="editingProvider.website" />
        </el-form-item>
        
        <el-divider>{{ t('keys.api_base_urls') }}</el-divider>
        
        <el-form-item label="OpenAI Base URL">
          <el-input v-model="editingProvider.openai_base_url" />
        </el-form-item>
        <el-form-item label="Gemini Base URL">
          <el-input v-model="editingProvider.gemini_base_url" />
        </el-form-item>
        <el-form-item label="Claude Base URL">
          <el-input v-model="editingProvider.claude_base_url" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditProviderDialog = false; editingProvider = null">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="updateProvider" :loading="loading">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
code {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
}
</style>
