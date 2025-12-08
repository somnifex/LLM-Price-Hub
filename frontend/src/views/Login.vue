<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const email = ref('')
const password = ref('')
const totpCode = ref('')
const loading = ref(false)
const totpRequired = ref(false)
const emailNotVerified = ref(false)
const resendLoading = ref(false)

const resendVerification = async () => {
  if (!email.value) {
    ElMessage.error(t('auth.email_required'))
    return
  }
  resendLoading.value = true
  try {
    await api.post('/auth/resend-verification', { email: email.value })
    ElMessage.success(t('auth.verification_sent'))
  } catch (e) {
    ElMessage.error(t('auth.register_failed'))
  } finally {
    resendLoading.value = false
  }
}

const handleLogin = async () => {
  loading.value = true
  try {
    await authStore.login(email.value, password.value, totpCode.value || undefined)
    ElMessage.success(t('auth.login_success'))
    router.push('/')
  } catch (e: any) {
    const code = e?.code
    if (code === 'TOTP_REQUIRED') {
      totpRequired.value = true
      ElMessage.warning(t('auth.totp_required'))
    } else if (code === 'EMAIL_NOT_VERIFIED') {
      emailNotVerified.value = true
      ElMessage.warning(t('auth.verify_email_first'))
    } else {
      ElMessage.error(t('auth.invalid_credentials'))
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="relative">
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute -top-24 left-10 w-72 h-72 bg-primary-200/60 blur-3xl"></div>
      <div class="absolute bottom-0 right-0 w-96 h-96 bg-secondary-200/50 blur-3xl"></div>
    </div>

    <div class="page-shell relative">
      <div class="page-hero p-6 md:p-8">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          <div class="space-y-4">
            <span class="pill-accent">{{ t('auth.login') }}</span>
            <h1 class="text-3xl md:text-4xl font-bold text-secondary-900">{{ t('auth.login') }}</h1>
            <p class="text-secondary-600 leading-relaxed">
              {{ t('home.subtitle') }}
            </p>
            <div class="flex flex-wrap gap-3 text-sm text-secondary-600">
              <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/70 border border-primary-100 shadow-sm">
                <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                {{ t('nav.admin') }}
              </div>
              <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/70 border border-primary-100 shadow-sm">
                <span class="h-2 w-2 rounded-full bg-secondary-400"></span>
                {{ t('nav.submit') }}
              </div>
            </div>
          </div>

          <div class="card-muted p-6 md:p-7 bg-white/90">
            <div class="section-header">
              <div>
                <p class="section-kicker mb-1">{{ t('auth.login') }}</p>
                <h3 class="text-xl font-semibold text-secondary-900">{{ t('auth.login') }}</h3>
              </div>
              <el-tag effect="light" type="success">{{ t('keys.security_tab') }}</el-tag>
            </div>

            <el-form label-position="top" @submit.prevent="handleLogin" class="space-y-4">
              <el-form-item :label="t('auth.email')">
                <el-input v-model="email" type="email" placeholder="example@mail.com" />
              </el-form-item>
              <el-form-item :label="t('auth.password')">
                <el-input v-model="password" type="password" show-password />
              </el-form-item>
              <el-form-item v-if="totpRequired" :label="t('auth.totp_code')">
                <el-input v-model="totpCode" />
              </el-form-item>

              <div class="space-y-3">
                <el-button type="primary" class="w-full h-11" @click="handleLogin" :loading="loading">
                  {{ t('auth.login') }}
                </el-button>
                <div class="flex items-center justify-between text-sm text-secondary-600">
                  <router-link to="/register" class="text-primary-600 hover:text-primary-700">{{ t('auth.create_account') }}</router-link>
                  <button type="button" class="text-secondary-500 hover:text-secondary-700" @click="emailNotVerified = true">
                    {{ t('auth.verify_email_first') }}
                  </button>
                </div>
              </div>

              <div v-if="emailNotVerified" class="space-y-2 rounded-xl border border-dashed border-primary-200 bg-primary-50/60 p-3">
                <div class="flex items-center justify-between">
                  <span class="font-medium text-secondary-800">{{ t('auth.verify_email_first') }}</span>
                  <el-tag type="warning" effect="light">{{ t('auth.verification_sent') }}</el-tag>
                </div>
                <el-button class="w-full" :loading="resendLoading" @click="resendVerification">
                  {{ t('auth.resend_verification') }}
                </el-button>
              </div>
            </el-form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
