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
    if (res.data?.email_verified === false) {
      ElMessage.success(t('auth.verification_sent'))
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
  <div class="flex items-center justify-center min-h-[80vh]">
    <el-card class="w-full max-w-md p-6">
      <h2 class="text-2xl font-bold mb-6 text-center">{{ t('auth.register') }}</h2>
      <el-form @submit.prevent="handleRegister">
        <el-form-item :label="t('auth.email')">
          <el-input v-model="email" type="email" />
        </el-form-item>
        <el-form-item :label="t('auth.password')">
          <el-input v-model="password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" class="w-full mt-4" @click="handleRegister" :loading="loading">
          {{ t('auth.register') }}
        </el-button>
        <div class="text-center mt-4">
          <router-link to="/login" class="text-primary-600 text-sm hover:text-primary-700">{{ t('auth.back_to_login') }}</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>
