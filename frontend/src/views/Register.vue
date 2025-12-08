<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const email = ref('')
const password = ref('')
const loading = ref(false)

const handleRegister = async () => {
  loading.value = true
  try {
    const res = await api.post('/auth/register', { 
        email: email.value, 
        password: password.value 
    })
    const emailVerified = res.data?.email_verified
    const message = res.data?.message
    if (message) {
      const lower = String(message).toLowerCase()
      const isVerification = lower.includes('verify') || lower.includes('verification')
      ElMessage[isVerification ? 'info' : 'success'](isVerification ? t('auth.verification_sent') : message)
    } else if (emailVerified === false) {
      ElMessage.info(t('auth.verification_sent'))
    } else {
      ElMessage.success(t('auth.register_success'))
    }
    router.push('/login')
  } catch (e: any) {
    let msg = e.response?.data?.detail
    if (Array.isArray(msg)) {
      msg = msg.map((err: any) => err.msg).join(', ')
    }
    ElMessage.error(msg || t('auth.register_failed'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="relative">
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute -top-24 right-6 w-72 h-72 bg-primary-200/60 blur-3xl"></div>
      <div class="absolute bottom-0 left-0 w-96 h-96 bg-secondary-200/50 blur-3xl"></div>
    </div>

    <div class="page-shell relative">
      <div class="page-hero p-6 md:p-8">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          <div class="space-y-4">
            <span class="pill-accent">{{ t('auth.register') }}</span>
            <h1 class="text-3xl md:text-4xl font-bold text-secondary-900">{{ t('auth.create_account') }}</h1>
            <p class="text-secondary-600 leading-relaxed">
              {{ t('home.subtitle') }}
            </p>
            <div class="flex flex-wrap gap-3 text-sm text-secondary-600">
              <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/70 border border-primary-100 shadow-sm">
                <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                {{ t('nav.submit') }}
              </div>
              <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/70 border border-primary-100 shadow-sm">
                <span class="h-2 w-2 rounded-full bg-secondary-400"></span>
                {{ t('nav.settings') }}
              </div>
            </div>
          </div>

          <div class="card-muted p-6 md:p-7 bg-white/90">
            <div class="section-header">
              <div>
                <p class="section-kicker mb-1">{{ t('auth.register') }}</p>
                <h3 class="text-xl font-semibold text-secondary-900">{{ t('auth.create_account') }}</h3>
              </div>
              <el-tag effect="light" type="primary">{{ t('auth.login') }}</el-tag>
            </div>

            <el-form label-position="top" @submit.prevent="handleRegister" class="space-y-4">
              <el-form-item :label="t('auth.email')">
                <el-input v-model="email" type="email" />
              </el-form-item>
              <el-form-item :label="t('auth.password')">
                <el-input v-model="password" type="password" show-password />
              </el-form-item>

              <div class="space-y-3">
                <el-button type="primary" class="w-full h-11" @click="handleRegister" :loading="loading">
                  {{ t('auth.register') }}
                </el-button>
                <div class="flex items-center justify-between text-sm text-secondary-600">
                  <router-link to="/login" class="text-primary-600 hover:text-primary-700">{{ t('auth.back_to_login') }}</router-link>
                </div>
              </div>
            </el-form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
