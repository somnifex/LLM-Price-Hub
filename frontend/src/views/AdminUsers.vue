<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const users = ref([])
const loading = ref(false)
const authStore = useAuthStore()

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/users')
    users.value = res.data
  } catch (e) {
    ElMessage.error(t('admin.failed_fetch_users'))
  } finally {
    loading.value = false
  }
}

const updateUserRole = async (userId: number, role: string) => {
    try {
        await api.put(`/admin/users/${userId}/role`, { role })
        ElMessage.success(t('admin.role_updated'))
        fetchUsers()
    } catch (e) {
        ElMessage.error(t('admin.failed_update_role'))
    }
}

onMounted(fetchUsers)
</script>

<template>
  <el-card>
    <template #header>
      <div class="flex justify-between items-center">
        <span class="text-xl font-bold">{{ t('admin.user_management') }}</span>
      </div>
    </template>
    <el-table :data="users" v-loading="loading">
      <el-table-column prop="id" :label="t('admin.id')" width="60" />
      <el-table-column prop="email" :label="t('admin.email')" />
      <el-table-column prop="role" :label="t('admin.role')">
         <template #default="{ row }">
             <el-tag :type="row.role === 'super_admin' ? 'danger' : row.role === 'admin' ? 'warning' : 'info'">{{ row.role }}</el-tag>
         </template>
      </el-table-column>
      <el-table-column :label="t('admin.actions')" v-if="authStore.isSuperAdmin">
        <template #default="{ row }">
           <div v-if="row.role !== 'super_admin'">
               <el-button size="small" @click="updateUserRole(row.id, 'admin')" v-if="row.role !== 'admin'">{{ t('admin.make_admin') }}</el-button>
               <el-button size="small" @click="updateUserRole(row.id, 'user')" v-if="row.role !== 'user'">{{ t('admin.demote_user') }}</el-button>
           </div>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
