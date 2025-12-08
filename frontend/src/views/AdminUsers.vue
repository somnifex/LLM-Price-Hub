<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { computed } from 'vue'

const { t } = useI18n()
const users = ref([])
const loading = ref(false)
const authStore = useAuthStore()
const reviewDialogVisible = ref(false)
const selectedUser = ref<any>(null)
const userReviews = ref<any[]>([])
const reviewsLoading = ref(false)
const activeCount = computed(() => users.value.filter((u: any) => u.is_active).length)
const suspendedCount = computed(() => users.value.filter((u: any) => !u.is_active).length)

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

const canModerate = (role: string) => authStore.isSuperAdmin || role === 'user'

const updateUserRole = async (userId: number, role: string) => {
    try {
        await api.put(`/admin/users/${userId}/role`, { role })
        ElMessage.success(t('admin.role_updated'))
        fetchUsers()
    } catch (e) {
        ElMessage.error(t('admin.failed_update_role'))
    }
}

const suspendUser = async (user: any) => {
  if (!canModerate(user.role)) return
  try {
    const { value } = await ElMessageBox.prompt(
      t('admin.suspend_reason_placeholder'),
      t('admin.suspend_user_title'),
      {
        confirmButtonText: t('admin.suspend'),
        cancelButtonText: t('submit.cancel_btn'),
        inputPlaceholder: t('admin.suspend_reason_placeholder'),
      }
    )
    await api.post(`/admin/users/${user.id}/suspend`, { reason: value || t('admin.suspended_by_admin') })
    ElMessage.success(t('admin.user_suspended'))
    fetchUsers()
  } catch (e: any) {
    if (e === 'cancel' || e?.action === 'cancel') return
    ElMessage.error(t('admin.failed_suspend_user'))
  }
}

const restoreUser = async (user: any) => {
  if (!canModerate(user.role)) return
  try {
    await ElMessageBox.confirm(t('admin.restore_user_confirm'), t('admin.restore'), {
      confirmButtonText: t('admin.restore'),
      cancelButtonText: t('submit.cancel_btn'),
      type: 'success'
    })
    await api.post(`/admin/users/${user.id}/restore`)
    ElMessage.success(t('admin.user_restored'))
    fetchUsers()
  } catch (e: any) {
    if (e === 'cancel' || e?.action === 'cancel') return
    ElMessage.error(t('admin.failed_restore_user'))
  }
}

const deleteUser = async (user: any) => {
  if (!canModerate(user.role)) return
  try {
    await ElMessageBox.confirm(
      t('admin.delete_user_confirm'),
      t('admin.delete_user'),
      { confirmButtonText: t('admin.delete_user'), cancelButtonText: t('submit.cancel_btn'), type: 'warning' }
    )
    await api.delete(`/admin/users/${user.id}`)
    ElMessage.success(t('admin.user_deleted'))
    fetchUsers()
  } catch (e: any) {
    if (e === 'cancel' || e?.action === 'cancel') return
    ElMessage.error(t('admin.failed_delete_user'))
  }
}

const loadReviews = async (userId: number) => {
  reviewsLoading.value = true
  try {
    const res = await api.get(`/admin/users/${userId}/reviews`)
    userReviews.value = res.data
  } catch (e) {
    ElMessage.error(t('admin.failed_fetch_reviews'))
  } finally {
    reviewsLoading.value = false
  }
}

const openReviews = async (user: any) => {
  selectedUser.value = user
  reviewDialogVisible.value = true
  await loadReviews(user.id)
}

const deleteReview = async (reviewId: number) => {
  if (!selectedUser.value) return
  try {
    await ElMessageBox.confirm(
      t('admin.delete_review_confirm'),
      t('admin.remove_review'),
      { confirmButtonText: t('admin.remove_review'), cancelButtonText: t('submit.cancel_btn'), type: 'warning' }
    )
    await api.delete(`/admin/users/${selectedUser.value.id}/reviews/${reviewId}`)
    ElMessage.success(t('admin.review_deleted'))
    await Promise.all([loadReviews(selectedUser.value.id), fetchUsers()])
  } catch (e: any) {
    if (e === 'cancel' || e?.action === 'cancel') return
    ElMessage.error(t('admin.failed_remove_review'))
  }
}

const formatDate = (value?: string) => {
  if (!value) return '--'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

onMounted(fetchUsers)
</script>

<template>
  <div class="panel p-6 space-y-4">
    <div class="section-header">
      <div>
        <p class="section-kicker mb-1">{{ t('admin.user_management') }}</p>
        <h3 class="text-xl font-semibold text-secondary-900">{{ t('admin.user_overview') }}</h3>
        <p class="muted-subtitle">{{ t('admin.user_actions_hint') }}</p>
      </div>
      <div class="action-row">
        <el-tag type="success" effect="plain">{{ t('admin.status_active') }}: {{ activeCount }}</el-tag>
        <el-tag type="warning" effect="plain">{{ t('admin.status_suspended') }}: {{ suspendedCount }}</el-tag>
        <el-tag type="info" effect="plain">ID max: {{ Math.max(...users.map((u: any) => u.id || 0), 0) }}</el-tag>
      </div>
    </div>

    <el-table :data="users" v-loading="loading" class="rounded-2xl overflow-hidden border border-gray-100">
      <el-table-column prop="id" :label="t('admin.id')" width="80" />
      <el-table-column prop="email" :label="t('admin.email')" />
      <el-table-column prop="role" :label="t('admin.role')" width="160">
         <template #default="{ row }">
             <el-tag :type="row.role === 'super_admin' ? 'danger' : row.role === 'admin' ? 'warning' : 'info'">{{ row.role }}</el-tag>
         </template>
      </el-table-column>
      <el-table-column :label="t('admin.status')" width="200">
        <template #default="{ row }">
          <div class="flex flex-col gap-1">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? t('admin.status_active') : t('admin.status_suspended') }}
            </el-tag>
            <div v-if="!row.is_active && row.suspension_reason" class="text-xs text-secondary-500">
              {{ row.suspension_reason }}
            </div>
            <div v-if="row.suspended_until" class="text-xs text-secondary-400">
              {{ t('admin.suspended_until') }}: {{ formatDate(row.suspended_until) }}
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="t('admin.contributions')" width="220">
        <template #default="{ row }">
          <div class="text-xs text-secondary-600 space-y-1">
            <div>{{ t('admin.review_count', { count: row.review_count || 0 }) }}</div>
            <div>{{ t('admin.price_count', { count: row.price_count || 0 }) }}</div>
            <div class="text-secondary-400">{{ t('admin.created_at') }}: {{ formatDate(row.created_at) }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="t('admin.actions')">
        <template #default="{ row }">
           <div class="flex flex-wrap gap-2">
               <template v-if="authStore.isSuperAdmin && row.role !== 'super_admin'">
                 <el-button size="small" @click="updateUserRole(row.id, 'admin')" v-if="row.role !== 'admin'">{{ t('admin.make_admin') }}</el-button>
                 <el-button size="small" @click="updateUserRole(row.id, 'user')" v-if="row.role !== 'user'">{{ t('admin.demote_user') }}</el-button>
               </template>
               <el-button size="small" @click="openReviews(row)" :disabled="!canModerate(row.role)">
                 {{ t('admin.view_reviews') }}
               </el-button>
               <el-button
                size="small"
                type="warning"
                plain
                v-if="row.is_active"
                :disabled="!canModerate(row.role)"
                @click="suspendUser(row)"
               >
                {{ t('admin.suspend') }}
               </el-button>
               <el-button
                size="small"
                type="success"
                plain
                v-else
                :disabled="!canModerate(row.role)"
                @click="restoreUser(row)"
               >
                {{ t('admin.restore') }}
               </el-button>
               <el-button
                size="small"
                type="danger"
                plain
                :disabled="!canModerate(row.role)"
                @click="deleteUser(row)"
               >
                {{ t('admin.delete_user') }}
               </el-button>
           </div>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="reviewDialogVisible"
      :title="t('admin.reviews_for_user', { email: selectedUser?.email || '' })"
      width="90vw"
      append-to-body
      top="4vh"
      destroy-on-close
      class="reviews-dialog max-h-[90vh]"
    >
      <div class="space-y-4">
        <div class="reviews-hero">
          <div>
            <p class="section-kicker mb-1">{{ t('admin.user_management') }}</p>
            <h2 class="text-2xl font-semibold text-secondary-900">
              {{ t('admin.reviews_for_user', { email: selectedUser?.email || '' }) }}
            </h2>
            <p class="text-secondary-600 text-sm mt-1">
              {{ t('admin.review_count', { count: userReviews.length }) }}
            </p>
          </div>
          <div class="flex items-center gap-2 text-secondary-700 text-sm">
            <el-tag size="large" effect="light">{{ selectedUser?.role || 'user' }}</el-tag>
            <el-tag :type="selectedUser?.is_active ? 'success' : 'warning'" effect="light">
              {{ selectedUser?.is_active ? t('admin.status_active') : t('admin.status_suspended') }}
            </el-tag>
          </div>
        </div>

        <div class="rounded-2xl border border-primary-100 bg-white/90 shadow-[0_14px_50px_-24px_rgba(15,23,42,0.35)] overflow-hidden">
          <el-table :data="userReviews" v-loading="reviewsLoading" size="small" height="60vh">
            <el-table-column prop="provider_name" :label="t('admin.provider')" />
            <el-table-column prop="rating" :label="t('admin.rating')" width="120" />
            <el-table-column prop="comment" :label="t('admin.comment')" />
            <el-table-column prop="created_at" :label="t('admin.created_at')" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column :label="t('admin.actions')" width="160">
              <template #default="{ row }">
                <el-button size="small" type="danger" plain @click="deleteReview(row.id)">{{ t('admin.remove_review') }}</el-button>
              </template>
            </el-table-column>
            <template #empty>
              <div class="text-secondary-500 text-sm py-6">{{ t('admin.no_reviews') }}</div>
            </template>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.reviews-dialog :deep(.el-dialog) {
  background: radial-gradient(circle at 10% 20%, rgba(5, 150, 105, 0.12), transparent 24%),
    radial-gradient(circle at 80% 0%, rgba(100, 116, 139, 0.08), transparent 20%),
    #f8fafc;
  border-radius: 18px;
  border: 1px solid rgba(5, 150, 105, 0.18);
  max-width: 1180px;
  width: 90vw;
}

.reviews-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 16px 20px 0 20px;
  border-bottom: 1px solid rgba(5, 150, 105, 0.1);
}

.reviews-dialog :deep(.el-dialog__body) {
  padding: 12px 20px 20px 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.96));
}

.reviews-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 16px;
  background: linear-gradient(120deg, rgba(5, 150, 105, 0.12), rgba(100, 116, 139, 0.12));
  border: 1px solid rgba(5, 150, 105, 0.18);
}

.reviews-dialog :deep(.el-table__header-wrapper) {
  background: transparent;
}

.reviews-dialog :deep(.el-table th) {
  background: rgba(255, 255, 255, 0.9);
}
</style>
