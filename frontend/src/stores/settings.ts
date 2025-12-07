import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import { useAuthStore } from './auth'

export const useSettingsStore = defineStore('settings', () => {
    const currencies = ref<any[]>([])
    const userSettings = ref({
        preferred_currencies: ['USD'],
        default_currency: 'USD'
    })
    const loading = ref(false)

    const authStore = useAuthStore()

    async function fetchCurrencies() {
        try {
            const res = await api.get('/settings/currencies')
            currencies.value = res.data
        } catch (e) {
            console.error('Failed to fetch currencies', e)
        }
    }

    async function fetchUserSettings() {
        if (!authStore.isAuthenticated) return
        try {
            const res = await api.get('/settings/user')
            const data = res.data
            
            let preferred = ['USD']
            if (data.preferred_currencies) {
                try {
                    preferred = JSON.parse(data.preferred_currencies)
                } catch (e) {
                    console.error('Failed to parse preferred currencies', e)
                }
            }

            userSettings.value = {
                preferred_currencies: preferred,
                default_currency: data.default_currency || 'USD'
            }
        } catch (e) {
            console.error('Failed to fetch user settings', e)
        }
    }

    async function updateUserSettings(preferred: string[], defaultCurr: string) {
        loading.value = true
        try {
            const payload = {
                preferred_currencies: preferred,
                default_currency: defaultCurr
            }
            await api.put('/settings/user', payload)
            userSettings.value = payload
        } catch (e) {
            console.error('Failed to update settings', e)
            throw e
        } finally {
            loading.value = false
        }
    }

    const availableCurrencies = computed(() => currencies.value)
    
    const preferredCurrencyList = computed(() => {
        return currencies.value.filter(c => userSettings.value.preferred_currencies.includes(c.code))
    })

    const currentCurrencyRate = computed(() => {
        const code = userSettings.value.default_currency
        const curr = currencies.value.find(c => c.code === code)
        return curr ? curr.rate_to_usd : 1.0
    })

    function convertPrice(priceInUsd: number, targetCurrency?: string): string {
        const code = targetCurrency || userSettings.value.default_currency
        const curr = currencies.value.find(c => c.code === code)
        const rate = curr ? curr.rate_to_usd : 1.0
        
        const converted = priceInUsd * rate
        
        // Format logic
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: code,
            minimumFractionDigits: 2,
            maximumFractionDigits: 6
        }).format(converted)
    }

    return {
        currencies,
        userSettings,
        loading,
        fetchCurrencies,
        fetchUserSettings,
        updateUserSettings,
        availableCurrencies,
        preferredCurrencyList,
        currentCurrencyRate,
        convertPrice
    }
})
