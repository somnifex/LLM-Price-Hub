<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Settings {
    site_name?: string
    maintenance_mode?: string
    exchange_rate_provider?: string
    exchange_rate_url?: string
    exchange_rate_key?: string
    exchange_rate_interval_minutes?: string
    smtp_host?: string
    smtp_port?: string
    smtp_username?: string
    smtp_password?: string
    smtp_use_tls?: string
    smtp_use_ssl?: string
    smtp_sender?: string
    force_email_verification?: string
    home_display_mode?: string
    [key: string]: string | undefined
}

const settings = ref<Settings>({})
const loading = ref(false)
const saving = ref(false)
const saveStatus = ref<'idle' | 'success' | 'error'>('idle')
const lastSavedAt = ref<string | null>(null)

const providerOptions = [
    { label: 'ExchangeRate-API (Free/Pro)', value: 'exchangerate-api' },
    { label: 'Fixer.io', value: 'fixer' },
    { label: 'Open Exchange Rates', value: 'openexchangerates' },
    { label: 'Custom', value: 'custom' }
]

const displayOptions = [
    { label: 'Table', value: 'table' },
    { label: 'Cards', value: 'cards' },
    { label: 'Chart', value: 'chart' }
]

const onProviderChange = () => {
    const p = settings.value.exchange_rate_provider
    if (p === 'exchangerate-api') {
        settings.value.exchange_rate_url = 'https://v6.exchangerate-api.com/v6/{KEY}/latest/USD'
    } else if (p === 'fixer') {
        settings.value.exchange_rate_url = 'http://data.fixer.io/api/latest?access_key={KEY}'
    } else if (p === 'openexchangerates') {
        settings.value.exchange_rate_url = 'https://openexchangerates.org/api/latest.json?app_id={KEY}'
    } else if (p === 'custom') {
        settings.value.exchange_rate_url = ''
    }
}

const fetchSettings = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/settings')
    settings.value = res.data
    // If empty, init with some defaults for demo
    if (Object.keys(settings.value).length === 0) {
        settings.value = { 
            site_name: 'LLM Price Hub', 
            maintenance_mode: 'false',
                        exchange_rate_provider: 'custom',
                        smtp_use_tls: 'true',
                        smtp_use_ssl: 'false',
                        force_email_verification: 'false',
                        home_display_mode: 'table'
        }
    }
    if (!settings.value.exchange_rate_provider) {
        settings.value.exchange_rate_provider = 'custom'
    }
        if (!settings.value.smtp_use_tls) settings.value.smtp_use_tls = 'true'
        if (!settings.value.smtp_use_ssl) settings.value.smtp_use_ssl = 'false'
        if (!settings.value.force_email_verification) settings.value.force_email_verification = 'false'
        if (!settings.value.home_display_mode) settings.value.home_display_mode = 'table'
  } catch (e) {
    ElMessage.error(t('admin.failed_fetch_settings'))
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
    saving.value = true
    saveStatus.value = 'idle'
    try {
        await api.put('/admin/settings', settings.value)
        saveStatus.value = 'success'
        lastSavedAt.value = new Date().toISOString()
        ElMessage.success(t('admin.settings_saved'))
    } catch (e) {
        saveStatus.value = 'error'
        ElMessage.error(t('admin.failed_save_settings'))
    } finally {
        saving.value = false
    }
}

onMounted(fetchSettings)

const savedText = computed(() => {
    if (!lastSavedAt.value) return ''
    return new Date(lastSavedAt.value).toLocaleString()
})
</script>

<template>
  <div class="space-y-6" v-loading="loading">
    <div class="page-hero p-6 md:p-7">
      <div class="section-header">
        <div>
          <p class="section-kicker mb-1">{{ t('admin.settings') }}</p>
          <h2 class="text-2xl font-bold text-secondary-900">{{ t('admin.settings_header') }}</h2>
          <p class="muted-subtitle">{{ t('admin.settings_overview') }}</p>
        </div>
        <div class="action-row">
          <el-tag type="success" effect="light">{{ t('admin.site_block') }}</el-tag>
          <el-tag type="warning" effect="light">{{ t('admin.smtp_config') }}</el-tag>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="panel p-6 space-y-4">
        <div class="section-header">
          <div>
            <p class="section-kicker mb-1">{{ t('admin.site_block') }}</p>
            <h3 class="text-xl font-semibold text-secondary-900">{{ t('admin.site_name') }}</h3>
            <p class="muted-subtitle">{{ t('admin.site_block_hint') }}</p>
          </div>
        </div>
        <el-form label-position="top">
          <el-form-item :label="t('admin.site_name')">
            <el-input v-model="settings.site_name" />
          </el-form-item>
        <el-form-item :label="t('admin.home_display_mode')">
            <el-select v-model="settings.home_display_mode">
                <el-option v-for="opt in displayOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
            <p class="text-xs text-secondary-500 mt-1">{{ t('admin.home_display_hint') }}</p>
        </el-form-item>
          <el-form-item :label="t('admin.maintenance')">
            <div class="flex items-center justify-between w-full">
              <span class="muted-subtitle">{{ t('admin.maintenance') }}</span>
              <el-switch v-model="settings.maintenance_mode" active-value="true" inactive-value="false" />
            </div>
          </el-form-item>
          <el-form-item :label="t('admin.force_email_verification')">
            <div class="flex items-center justify-between w-full">
              <span class="muted-subtitle">{{ t('admin.force_email_verification') }}</span>
              <el-switch v-model="settings.force_email_verification" active-value="true" inactive-value="false" />
            </div>
          </el-form-item>
        </el-form>
      </div>

      <div class="panel p-6 space-y-4">
        <div class="section-header">
          <div>
            <p class="section-kicker mb-1">{{ t('admin.exchange_config') }}</p>
            <h3 class="text-xl font-semibold text-secondary-900">{{ t('admin.provider') }}</h3>
            <p class="muted-subtitle">{{ t('admin.exchange_hint') }}</p>
          </div>
        </div>
        <el-form label-position="top">
          <el-form-item :label="t('admin.provider')">
            <el-select v-model="settings.exchange_rate_provider" @change="onProviderChange" :placeholder="t('admin.select_provider')">
              <el-option v-for="opt in providerOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('admin.api_url')">
            <el-input v-model="settings.exchange_rate_url" placeholder="https://api.exchangerate-api.com/v4/latest/USD" />
          </el-form-item>
          <el-form-item :label="t('admin.api_key')">
            <el-input v-model="settings.exchange_rate_key" type="password" show-password />
          </el-form-item>
          <el-form-item :label="t('admin.interval')">
            <el-input v-model="settings.exchange_rate_interval_minutes" type="number" />
          </el-form-item>
        </el-form>
      </div>
    </div>

    <div class="panel p-6 space-y-4">
      <div class="section-header">
        <div>
          <p class="section-kicker mb-1">{{ t('admin.smtp_config') }}</p>
          <h3 class="text-xl font-semibold text-secondary-900">{{ t('admin.email_delivery') }}</h3>
          <p class="muted-subtitle">{{ t('admin.smtp_hint') }}</p>
        </div>
        <el-tag type="info" effect="plain">{{ t('admin.smtp_tls_ssl') }}</el-tag>
      </div>
      <el-alert :closable="false" type="info">
        {{ t('admin.smtp_hint') }}
      </el-alert>
      <el-form label-position="top">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <el-form-item :label="t('admin.smtp_host')">
            <el-input v-model="settings.smtp_host" placeholder="smtp.example.com" />
          </el-form-item>
          <el-form-item :label="t('admin.smtp_port')">
            <el-input v-model="settings.smtp_port" type="number" />
          </el-form-item>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <el-form-item :label="t('admin.smtp_username')">
            <el-input v-model="settings.smtp_username" />
          </el-form-item>
          <el-form-item :label="t('admin.smtp_password')">
            <el-input v-model="settings.smtp_password" type="password" show-password />
          </el-form-item>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <el-form-item :label="t('admin.smtp_sender')">
            <el-input v-model="settings.smtp_sender" placeholder="no-reply@example.com" />
          </el-form-item>
          <el-form-item :label="t('admin.smtp_tls_ssl')">
            <div class="flex items-center gap-6">
              <div class="flex items-center gap-2">
                <el-switch v-model="settings.smtp_use_tls" active-value="true" inactive-value="false" />
                <span class="text-sm text-gray-600">TLS</span>
              </div>
              <div class="flex items-center gap-2">
                <el-switch v-model="settings.smtp_use_ssl" active-value="true" inactive-value="false" />
                <span class="text-sm text-gray-600">SSL</span>
              </div>
            </div>
          </el-form-item>
        </div>
      </el-form>
    </div>

    <div class="panel p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
      <div>
        <p class="section-kicker mb-1">{{ t('admin.settings') }}</p>
        <p v-if="saveStatus === 'success' && savedText" class="muted-subtitle">
          {{ t('admin.last_saved_at', { time: savedText }) }}
        </p>
        <p v-else class="muted-subtitle">{{ t('admin.not_saved_yet') }}</p>
      </div>
      <div class="action-row">
        <el-tag v-if="saveStatus === 'success'" type="success" effect="plain">
          {{ t('admin.settings_saved') }}
        </el-tag>
        <el-tag v-else-if="saveStatus === 'error'" type="danger" effect="plain">
          {{ t('admin.failed_save_settings') }}
        </el-tag>
        <el-button type="primary" size="large" :loading="saving" @click="saveSettings">
          {{ t('admin.save') }}
        </el-button>
      </div>
    </div>
  </div>
</template>
