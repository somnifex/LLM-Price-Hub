import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || '')
    const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))


    const isAuthenticated = computed(() => !!token.value)
    const isAdmin = computed(() => ['admin', 'super_admin'].includes(user.value?.role))
    const isSuperAdmin = computed(() => user.value?.role === 'super_admin')

    function setToken(newToken: string) {
        token.value = newToken
        localStorage.setItem('token', newToken)
    }

    function setUser(userData: any) {
        user.value = userData
        localStorage.setItem('user', JSON.stringify(userData))
    }

    async function login(email: string, password: string, totpCode?: string) {
        const formData = new FormData()
        formData.append('username', email)
        formData.append('password', password)
        if (totpCode) {
            formData.append('totp_code', totpCode)
        }

        try {
            const res = await api.post('/auth/token', formData)
            setToken(res.data.access_token)

            const payload = JSON.parse(atob(res.data.access_token.split('.')[1]))
            setUser({ email: payload.sub, role: payload.role })
            return { ok: true }
        } catch (e: any) {
            let detail = e?.response?.data?.detail
            if (Array.isArray(detail)) {
                detail = detail.map((err: any) => err.msg).join(', ')
            }
            const err = new Error(detail || 'LOGIN_FAILED') as any
            err.code = detail || 'LOGIN_FAILED'
            throw err
        }
    }

    function logout() {
        token.value = ''
        user.value = null
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        // Router might not be available here depending on pinia init. 
        // Usually better to return or let component handle redirect.
        window.location.href = '/'
    }

    return { token, user, isAuthenticated, isAdmin, isSuperAdmin, login, logout, setUser }
})
