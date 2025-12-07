<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const authStore = useAuthStore()

const menuItems = [
    { key: 'content_moderation', path: '/admin/content', icon: 'Document' },
    { key: 'user_management', path: '/admin/users', icon: 'User', role: 'super_admin' },
    { key: 'settings', path: '/admin/settings', icon: 'Setting', role: 'super_admin' },
]

const filteredMenuItems = computed(() => {
    return menuItems.filter(item => !item.role || (item.role === 'super_admin' && authStore.isSuperAdmin))
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold text-gray-900">{{ t('admin.admin_panel') }}</h1>
    </div>

    <!-- Navigation -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 p-1 inline-flex">
        <div class="flex space-x-1">
            <router-link 
                v-for="item in filteredMenuItems" 
                :key="item.path" 
                :to="item.path"
                custom
                v-slot="{ navigate, isActive }"
            >
                <button 
                    @click="navigate"
                    :class="[
                        'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200',
                        isActive 
                            ? 'bg-primary-50 text-primary-700 shadow-sm' 
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    ]"
                >
                    <el-icon><component :is="item.icon" /></el-icon>
                    {{ t('admin.' + item.key) }}
                </button>
            </router-link>
        </div>
    </div>

    <!-- Content -->
    <router-view v-slot="{ Component }">
        <transition name="el-fade-in-linear" mode="out-in">
            <component :is="Component" />
        </transition>
    </router-view>
  </div>
</template>
