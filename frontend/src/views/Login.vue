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
  <div class="flex items-center justify-center min-h-[80vh]">
    <el-card class="w-full max-w-md p-6">
      <h2 class="text-2xl font-bold mb-6 text-center">{{ t('auth.login') }}</h2>
      <el-form @submit.prevent="handleLogin">
        <el-form-item :label="t('auth.email')">
          <el-input v-model="email" type="email" placeholder="example@mail.com" />
        </el-form-item>
        <el-form-item :label="t('auth.password')">
          <el-input v-model="password" type="password" show-password />
        </el-form-item>
        <el-form-item v-if="totpRequired" :label="t('auth.totp_code')">
          <el-input v-model="totpCode" />
        </el-form-item>
        <el-button type="primary" class="w-full mt-4" @click="handleLogin" :loading="loading">
          {{ t('auth.login') }}
        </el-button>
        <div v-if="emailNotVerified" class="mt-4 text-center">
          <el-alert type="warning" :closable="false">
            {{ t('auth.verify_email_first') }}
          </el-alert>
          <el-button class="w-full mt-2" :loading="resendLoading" @click="resendVerification">
            {{ t('auth.resend_verification') }}
          </el-button>
        </div>
        <div class="text-center mt-4">
          <router-link to="/register" class="text-primary-600 text-sm hover:text-primary-700">{{ t('auth.create_account') }}</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>
