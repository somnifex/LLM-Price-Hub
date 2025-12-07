<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const status = ref<'pending' | 'success' | 'error'>('pending')

const verify = async () => {
  const token = route.query.token as string
  if (!token) {
    status.value = 'error'
    return
  }
  try {
    await api.post('/auth/verify-email', null, { params: { token } })
    status.value = 'success'
    ElMessage.success(t('auth.login_success'))
    setTimeout(() => router.push('/login'), 1200)
  } catch (e) {
    status.value = 'error'
    ElMessage.error(t('auth.register_failed'))
  }
}

onMounted(verify)
</script>

<template>
  <div class="flex items-center justify-center min-h-[70vh]">
    <el-card class="w-full max-w-md text-center py-10">
      <div v-if="status === 'pending'">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="status === 'success'" class="space-y-3">
        <el-result icon="success" :title="t('auth.login_success')" :sub-title="t('auth.verify_email_first')" />
      </div>
      <div v-else class="space-y-3">
        <el-result icon="warning" title="Verification failed" sub-title="Please request a new verification email." />
        <el-button type="primary" @click="router.push('/login')">{{ t('auth.back_to_login') }}</el-button>
      </div>
    </el-card>
  </div>
</template>
