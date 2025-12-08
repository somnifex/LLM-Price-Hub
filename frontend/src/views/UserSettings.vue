<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
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

// Account security state
const passwordForm = reactive({
  newPassword: '',
  confirmPassword: '',
  emailCode: '',
  totpCode: '',
})
const emailForm = reactive({
  newEmail: '',
  emailCode: '',
  totpCode: '',
})
const passwordSaving = ref(false)
const emailSaving = ref(false)
const passwordCodeSending = ref(false)
const emailCodeSending = ref(false)

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

function getErrorMessage(error: any, fallback: string) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  return fallback
}

async function sendPasswordEmailCode() {
  passwordCodeSending.value = true
  try {
    await api.post('/account/request-code', { action: 'password_reset' })
    ElMessage.success(t('account.code_sent'))
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, t('settings.save_failed')))
  } finally {
    passwordCodeSending.value = false
  }
}

async function updatePassword() {
  if (passwordForm.newPassword.length < 8) {
    ElMessage.error(t('account.password_hint'))
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.error(t('keys.passwords_do_not_match'))
    return
  }
  if (!passwordForm.emailCode && !passwordForm.totpCode) {
    ElMessage.error(t('account.verification_required'))
    return
  }

  passwordSaving.value = true
  try {
    await api.post('/account/reset-password', {
      new_password: passwordForm.newPassword,
      code: passwordForm.emailCode || undefined,
      totp_code: passwordForm.totpCode || undefined,
    })
    ElMessage.success(t('account.password_updated'))
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    passwordForm.emailCode = ''
    passwordForm.totpCode = ''
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, t('settings.save_failed')))
  } finally {
    passwordSaving.value = false
  }
}

async function sendEmailChangeCode() {
  if (!emailForm.newEmail) {
    ElMessage.error(t('account.enter_new_email'))
    return
  }
  emailCodeSending.value = true
  try {
    await api.post('/account/request-code', { action: 'email_change', new_email: emailForm.newEmail })
    ElMessage.success(t('account.code_sent'))
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, t('settings.save_failed')))
  } finally {
    emailCodeSending.value = false
  }
}

async function updateEmail() {
  if (!emailForm.newEmail) {
    ElMessage.error(t('account.enter_new_email'))
    return
  }
  if (!emailForm.emailCode && !emailForm.totpCode) {
    ElMessage.error(t('account.verification_required'))
    return
  }
  emailSaving.value = true
  try {
    const res = await api.post('/account/change-email', {
      new_email: emailForm.newEmail,
      code: emailForm.emailCode || undefined,
      totp_code: emailForm.totpCode || undefined,
    })
    authStore.setUser({
      email: emailForm.newEmail.toLowerCase(),
      role: authStore.user?.role || 'user',
    })
    ElMessage.success(t('account.email_updated'))
    if (!res.data?.email_verified) {
      ElMessage.info(t('account.verify_new_email'))
    }
    emailForm.emailCode = ''
    emailForm.totpCode = ''
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, t('settings.save_failed')))
  } finally {
    emailSaving.value = false
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
    return '**************'
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

const openDisableTotpDialog = () => {
  totpCode.value = ''
  showDisableTotp.value = true
}

const toggleE2EEState = () => {
  if (e2eeEnabled.value) {
    disableE2EE()
  } else {
    showE2EESetup.value = true
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
  <div class="relative overflow-hidden bg-gradient-to-br from-primary-50 via-white to-secondary-50">
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute -top-20 right-0 w-80 h-80 bg-primary-200/50 blur-3xl"></div>
      <div class="absolute -bottom-16 -left-8 w-96 h-96 bg-secondary-200/50 blur-3xl"></div>
      <div class="absolute inset-0" style="background-image: radial-gradient(rgba(15,23,42,0.08) 1px, transparent 1px); background-size: 18px 18px;"></div>
    </div>

    <div class="relative page-shell">
      <div class="page-hero text-secondary-900">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-6">
          <div>
            <p class="section-kicker text-secondary-500 mb-2">{{ t('keys.user_settings') }}</p>
            <h1 class="text-3xl font-bold text-secondary-900">{{ authStore.user?.email || t('keys.user_settings') }}</h1>
            <p class="text-sm text-secondary-600">{{ t('keys.security_tab') }} / {{ t('keys.api_keys_tab') }} / {{ t('keys.channels_tab') }}</p>
          </div>
          <div class="action-row">
            <el-tag :type="totpEnabled ? 'success' : 'info'" effect="light">
              {{ totpEnabled ? t('keys.enabled') : t('keys.disabled') }}
            </el-tag>
            <el-button v-if="authStore.isAdmin" type="primary" @click="$router.push('/admin')">
              {{ t('keys.admin_dashboard') }}
            </el-button>
          </div>
        </div>
      </div>

      <div class="card-muted p-3 bg-white/90">
        <el-tabs v-model="activeTab" type="card">
          <!-- General Tab -->
          <el-tab-pane :label="t('settings.general_tab')" name="general">
            <div class="panel p-5 space-y-5">
              <div class="flex items-center justify-between">
                <div>
                  <p class="section-kicker mb-1">{{ t('settings.general_tab') }}</p>
                  <h3 class="text-xl font-semibold text-secondary-900">{{ t('settings.general_tab') }}</h3>
                  <p class="muted-subtitle">{{ t('settings.preferred_currencies') }}</p>
                </div>
              </div>
              
              <div class="space-y-4">
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

                <div class="action-row pt-2">
                  <el-button type="primary" :loading="settingsLoading" @click="saveGeneralSettings">
                    {{ t('settings.save') }}
                  </el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- Security Tab -->
          <el-tab-pane :label="t('keys.security_tab')" name="security">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div class="panel p-5 space-y-4 flex flex-col h-full">
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-xl font-semibold text-secondary-900">{{ t('keys.totp_title') }}</h3>
                    <p class="muted-subtitle">{{ t('keys.totp_description') }}</p>
                  </div>
                  <el-tag :type="totpEnabled ? 'success' : 'info'">{{ totpEnabled ? t('keys.enabled') : t('keys.disabled') }}</el-tag>
                </div>

                <div class="panel-body">
                  <el-alert v-if="totpEnabled" type="success" :closable="false">{{ t('keys.totp_active') }}</el-alert>
                  <div v-if="totpBackupCodes.length" class="mt-2 bg-gray-50 p-3 rounded">
                    <p class="font-semibold mb-2">{{ t('keys.backup_codes') }}</p>
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
                      <code v-for="code in totpBackupCodes" :key="code" class="block bg-white border px-2 py-1 rounded text-center">{{ code }}</code>
                    </div>
                    <p class="text-xs text-gray-500 mt-2">{{ t('keys.backup_codes_hint') }}</p>
                  </div>
                </div>

                <div class="panel-footer">
                  <el-button
                    :type="totpEnabled ? 'danger' : 'primary'"
                    :loading="totpLoading"
                    @click="totpEnabled ? openDisableTotpDialog() : startTotpSetup"
                  >
                    {{ totpEnabled ? t('keys.disable_totp') : t('keys.enable_totp') }}
                  </el-button>
                </div>
              </div>

              <div class="panel p-5 space-y-4 flex flex-col h-full">
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-xl font-semibold text-secondary-900">{{ t('keys.encryption_settings') }}</h3>
                    <p class="muted-subtitle">{{ t('keys.e2ee_description') }}</p>
                  </div>
                  <el-tag :type="e2eeEnabled ? 'success' : 'info'">{{ e2eeEnabled ? t('keys.enabled') : t('keys.disabled') }}</el-tag>
                </div>
                
                <div class="panel-body">
                  <el-alert v-if="e2eeEnabled" type="success" :closable="false">
                    {{ t('keys.e2ee_active') }}
                  </el-alert>
                </div>
                
                <div class="panel-footer">
                  <el-button :type="e2eeEnabled ? 'danger' : 'primary'" @click="toggleE2EEState()">
                    {{ e2eeEnabled ? t('keys.disable_encryption') : t('keys.enable_encryption') }}
                  </el-button>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
              <div class="panel p-5 space-y-4 flex flex-col h-full">
                <div class="section-header">
                  <div>
                    <p class="section-kicker mb-1">{{ t('account.password_heading') }}</p>
                    <h3 class="text-xl font-semibold text-secondary-900">{{ t('account.password_heading') }}</h3>
                    <p class="muted-subtitle">{{ t('account.password_hint') }}</p>
                  </div>
                  <el-tag type="info">{{ t('keys.security_tab') }}</el-tag>
                </div>
                <div class="panel-body">
                  <el-form label-position="top" @submit.prevent>
                    <el-form-item :label="t('account.new_password')">
                      <el-input v-model="passwordForm.newPassword" type="password" show-password />
                    </el-form-item>
                    <el-form-item :label="t('keys.confirm_password')">
                      <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
                    </el-form-item>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <el-form-item :label="t('account.email_code')">
                        <div class="flex gap-2 items-center">
                          <el-input class="flex-1 uniform-input" v-model="passwordForm.emailCode" maxlength="6" />
                          <el-button type="primary" :loading="passwordCodeSending" @click="sendPasswordEmailCode">
                            {{ t('account.request_password_code') }}
                          </el-button>
                        </div>
                      </el-form-item>
                      <el-form-item :label="t('account.totp_code')">
                        <el-input class="uniform-input" v-model="passwordForm.totpCode" maxlength="10" :placeholder="t('account.totp_optional')" />
                      </el-form-item>
                    </div>
                  </el-form>
                </div>
                <div class="panel-footer">
                  <el-button type="primary" :loading="passwordSaving" @click="updatePassword">
                    {{ t('settings.save') }}
                  </el-button>
                </div>
              </div>

              <div class="panel p-5 space-y-4 flex flex-col h-full">
                <div class="section-header">
                  <div>
                    <p class="section-kicker mb-1">{{ t('account.email_heading') }}</p>
                    <h3 class="text-xl font-semibold text-secondary-900">{{ t('account.email_heading') }}</h3>
                    <p class="muted-subtitle">{{ t('account.email_hint') }}</p>
                  </div>
                  <el-tag type="info">{{ t('account.current_email') }}: {{ authStore.user?.email }}</el-tag>
                </div>
                <div class="panel-body">
                  <el-form label-position="top" @submit.prevent>
                    <el-form-item :label="t('account.new_email')">
                      <el-input v-model="emailForm.newEmail" type="email" :placeholder="authStore.user?.email || 'you@example.com'" />
                    </el-form-item>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <el-form-item :label="t('account.email_code')">
                        <div class="flex gap-2 items-center">
                          <el-input class="flex-1 uniform-input" v-model="emailForm.emailCode" maxlength="6" />
                          <el-button type="primary" :loading="emailCodeSending" @click="sendEmailChangeCode">
                            {{ t('account.request_email_code') }}
                          </el-button>
                        </div>
                      </el-form-item>
                      <el-form-item :label="t('account.totp_code')">
                        <el-input class="uniform-input" v-model="emailForm.totpCode" maxlength="10" :placeholder="t('account.totp_optional')" />
                      </el-form-item>
                    </div>
                  </el-form>
                </div>
                <div class="panel-footer panel-footer--between">
                  <p class="text-xs text-secondary-500">{{ t('account.verification_required') }}</p>
                  <el-button type="primary" :loading="emailSaving" @click="updateEmail">
                    {{ t('account.update_email') }}
                  </el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- API Keys Tab -->
          <el-tab-pane :label="t('keys.api_keys_tab')" name="api_keys">
            <div class="panel p-5 space-y-4">
              <div class="section-header">
                <div>
                  <p class="section-kicker mb-1">{{ t('keys.api_keys_tab') }}</p>
                  <h3 class="text-xl font-semibold text-secondary-900">{{ t('keys.my_api_keys') }}</h3>
                  <p class="muted-subtitle">{{ t('keys.key_will_be_encrypted') }}</p>
                </div>
                <el-button type="primary" size="small" @click="showAddKeyDialog = true">
                  {{ t('keys.add_key') }}
                </el-button>
              </div>
              
              <el-table :data="apiKeys" v-loading="keysLoading" stripe class="rounded-xl overflow-hidden">
                <el-table-column :label="t('keys.provider')">
                  <template #default="{ row }">
                    <div class="whitespace-normal break-words">{{ row.provider_name || '-' }}</div>
                  </template>
                </el-table-column>
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
            </div>
          </el-tab-pane>

          <!-- Channels Tab -->
          <el-tab-pane :label="t('keys.channels_tab')" name="channels">
            <div class="panel p-5 space-y-4">
              <div class="section-header">
                <div>
                  <p class="section-kicker mb-1">{{ t('keys.channels_tab') }}</p>
                  <h3 class="text-xl font-semibold text-secondary-900">{{ t('keys.my_providers') }}</h3>
                  <p class="muted-subtitle">{{ t('keys.api_base_urls') }}</p>
                </div>
                <el-button type="primary" size="small" @click="showAddProviderDialog = true">
                  {{ t('keys.add_provider') }}
                </el-button>
              </div>
              
              <el-table :data="userProviders" v-loading="providersLoading" stripe class="rounded-xl overflow-hidden">
                <el-table-column :label="t('keys.provider_name')">
                  <template #default="{ row }">
                    <div class="whitespace-normal break-words">{{ row.name || '-' }}</div>
                  </template>
                </el-table-column>
                <el-table-column :label="t('keys.website')">
                  <template #default="{ row }">
                    <div class="whitespace-normal break-words">{{ row.website || '-' }}</div>
                  </template>
                </el-table-column>
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
                        <code class="flex-1 break-words">{{ row.openai_base_url }}</code>
                        <el-button size="small" :icon="CopyDocument" circle @click="copyToClipboard(row.openai_base_url, 'OpenAI URL')" />
                      </div>
                      <div v-if="row.gemini_base_url" class="flex items-center gap-1 text-xs">
                        <span class="text-gray-500">Gemini:</span>
                        <code class="flex-1 break-words">{{ row.gemini_base_url }}</code>
                        <el-button size="small" :icon="CopyDocument" circle @click="copyToClipboard(row.gemini_base_url, 'Gemini URL')" />
                      </div>
                      <div v-if="row.claude_base_url" class="flex items-center gap-1 text-xs">
                        <span class="text-gray-500">Claude:</span>
                        <code class="flex-1 break-words">{{ row.claude_base_url }}</code>
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
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>

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
</template>

<style scoped>
code {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
}

:deep(.el-dialog) {
  background: radial-gradient(circle at 12% 18%, rgba(5, 150, 105, 0.08), transparent 22%),
    radial-gradient(circle at 82% 0%, rgba(100, 116, 139, 0.08), transparent 20%),
    #f8fafc;
  border: 1px solid rgba(5, 150, 105, 0.16);
  box-shadow: var(--brand-shadow);
}

:deep(.el-dialog__header) {
  margin-right: 0;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(5, 150, 105, 0.12);
}

:deep(.el-dialog__footer) {
  border-top: 1px solid rgba(226, 232, 240, 0.9);
  padding-top: 12px;
}

.panel-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 1rem;
}

.panel-footer {
  margin-top: auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
}

.panel-footer--between {
  justify-content: space-between;
}

.uniform-input :deep(.el-input__inner) {
  min-height: 44px;
}
</style>
