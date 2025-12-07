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
            exchange_rate_provider: 'custom'
        }
    }
    if (!settings.value.exchange_rate_provider) {
        settings.value.exchange_rate_provider = 'custom'
    }
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

        <el-button type="primary" @click="saveSettings">{{ t('admin.save') }}</el-button>
    </el-form>
  </div>
</template>
