<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const authStore = useAuthStore()
const route = useRoute()

const menuItems = [
    { key: 'content_moderation', path: '/admin/content', icon: 'Document' },
    { key: 'user_management', path: '/admin/users', icon: 'User', role: 'super_admin' },
    { key: 'settings', path: '/admin/settings', icon: 'Setting', role: 'super_admin' },
]

const activeIndex = route.path
</script>

<template>
  <div class="flex h-screen bg-gray-100">
      <!-- Sidebar -->
      <div class="w-64 bg-white shadow-md flex flex-col">
          <div class="p-6 border-b">
              <h1 class="text-2xl font-bold text-red-600">{{ t('admin.admin_panel') }}</h1>
          </div>
          <el-menu :default-active="activeIndex" router class="flex-1 border-r-0">
              <template v-for="item in menuItems" :key="item.path">
                   <el-menu-item :index="item.path" v-if="!item.role || (item.role === 'super_admin' && authStore.isSuperAdmin)">
                      <el-icon><component :is="item.icon" /></el-icon>
                      <span>{{ t('admin.' + item.key) }}</span>
                  </el-menu-item>
              </template>
          </el-menu>
          <div class="p-4 border-t">
              <div class="text-sm text-gray-500 mb-2">{{ t('admin.logged_in_as') }} {{ authStore.user?.email }}</div>
              <el-button type="danger" plain class="w-full" @click="authStore.logout">{{ t('nav.logout') }}</el-button>
          </div>
      </div>

      <!-- Main Content -->
      <div class="flex-1 overflow-auto p-8">
          <router-view></router-view>
      </div>
  </div>
</template>
