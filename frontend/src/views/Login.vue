<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const email = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  try {
    await authStore.login(email.value, password.value)
    ElMessage.success(t('auth.login_success'))
    router.push('/')
  } catch (e) {
    ElMessage.error(t('auth.invalid_credentials'))
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
        <el-button type="primary" class="w-full mt-4" @click="handleLogin" :loading="loading">
          {{ t('auth.login') }}
        </el-button>
        <div class="text-center mt-4">
          <router-link to="/register" class="text-blue-500 text-sm">{{ t('auth.create_account') }}</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>
