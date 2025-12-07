<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
    try {
        await api.put('/admin/settings', settings.value)
        ElMessage.success(t('admin.settings_saved'))
    } catch (e) {
        ElMessage.error(t('admin.failed_save_settings'))
    }
}

onMounted(fetchSettings)
</script>

<template>
  <div class="max-w-xl">
    <h3 class="text-xl font-bold mb-4">{{ t('admin.settings') }}</h3>
    <el-form label-position="top" v-loading="loading">
        <el-form-item :label="t('admin.site_name')">
            <el-input v-model="settings.site_name" />
        </el-form-item>
        <el-form-item :label="t('admin.maintenance')">
            <el-switch v-model="settings.maintenance_mode" active-value="true" inactive-value="false" />
        </el-form-item>

        <div class="my-6 border-t border-gray-200 pt-6">
            <h4 class="text-lg font-bold mb-4">{{ t('admin.smtp_config') }}</h4>
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
            <el-alert type="info" :closable="false" class="mb-2">
              {{ t('admin.smtp_hint') }}
            </el-alert>
            <el-form-item :label="t('admin.force_email_verification')">
                <el-switch v-model="settings.force_email_verification" active-value="true" inactive-value="false" />
            </el-form-item>
        </div>

        <div class="my-6 border-t border-gray-200 pt-6">
            <h4 class="text-lg font-bold mb-4">{{ t('admin.exchange_config') }}</h4>
            
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
        </div>

        <div class="my-6 border-t border-gray-200 pt-6">
            <h4 class="text-lg font-bold mb-4">{{ t('admin.home_display') }}</h4>
            <el-form-item :label="t('admin.home_display_mode')">
                <el-select v-model="settings.home_display_mode">
                    <el-option v-for="opt in displayOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
            </el-form-item>
            <el-alert type="info" :closable="false">{{ t('admin.home_display_hint') }}</el-alert>
        </div>

        <el-button type="primary" @click="saveSettings">{{ t('admin.save') }}</el-button>
    </el-form>
  </div>
</template>
