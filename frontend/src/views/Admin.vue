<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const authStore = useAuthStore()

const menuItems = [
    { key: 'content_moderation', path: '/admin/content', icon: 'Document' },
    { key: 'user_management', path: '/admin/users', icon: 'User', role: 'admin' },
    { key: 'settings', path: '/admin/settings', icon: 'Setting', role: 'super_admin' },
]

const filteredMenuItems = computed(() => {
    return menuItems.filter(item => {
      if (!item.role) return true
      if (item.role === 'admin') return authStore.isAdmin
      if (item.role === 'super_admin') return authStore.isSuperAdmin
      return false
    })
})
</script>

<template>
  <div class="relative min-h-screen overflow-hidden bg-gradient-to-br from-primary-50 via-white to-secondary-50 text-secondary-900">
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute -top-24 -left-10 w-72 h-72 bg-primary-200/50 blur-3xl"></div>
      <div class="absolute bottom-0 right-0 w-96 h-96 bg-secondary-200/50 blur-3xl"></div>
      <div class="absolute inset-0" style="background-image: radial-gradient(rgba(15,23,42,0.06) 1px, transparent 1px); background-size: 18px 18px;"></div>
    </div>

    <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">
      <div class="relative overflow-hidden rounded-3xl border border-primary-100 bg-gradient-to-r from-white via-primary-50 to-secondary-50 shadow-[0_24px_80px_-40px_rgba(15,23,42,0.45)] p-7 md:p-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <p class="section-kicker text-secondary-500 mb-2">{{ t('admin.admin_panel') }}</p>
            <h1 class="text-3xl md:text-4xl font-bold tracking-tight mb-3 text-secondary-900">{{ t('admin.admin_panel') }}</h1>
            <p class="text-sm md:text-base text-secondary-600">
              {{ t('admin.settings') }} · {{ t('admin.user_management') }} · {{ t('admin.pending_prices') }}
            </p>
          </div>
          <div class="flex flex-col md:items-end gap-3">
            <div class="inline-flex items-center gap-2 rounded-full border border-primary-100 bg-white/80 px-4 py-2 text-sm font-semibold text-secondary-800 shadow-sm">
              <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span class="uppercase tracking-[0.2em] text-xs text-secondary-500">Control</span>
              <span class="text-secondary-800">{{ authStore.user?.role || 'admin' }}</span>
            </div>
            <div class="flex gap-2 text-xs text-secondary-500">
              <span class="px-3 py-1 rounded-full bg-white/80 border border-primary-100">{{ t('admin.settings') }}</span>
              <span class="px-3 py-1 rounded-full bg-white/80 border border-primary-100">{{ t('admin.user_management') }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="panel p-2 shadow-lg shadow-primary-200/60">
        <div class="flex flex-wrap gap-2">
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
                'group flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200',
                isActive 
                  ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/30 scale-[1.01]' 
                  : 'bg-white/60 text-secondary-700 hover:bg-white hover:text-secondary-900 border border-transparent'
              ]"
            >
              <el-icon class="text-base"><component :is="item.icon" /></el-icon>
              {{ t('admin.' + item.key) }}
            </button>
          </router-link>
        </div>
      </div>

      <div class="pb-10">
        <router-view v-slot="{ Component }">
          <transition name="el-fade-in-linear" mode="out-in">
              <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>
