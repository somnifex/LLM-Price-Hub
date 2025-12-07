<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const { t, locale } = useI18n()
const authStore = useAuthStore()
const router = useRouter()

const switchLang = (lang: string) => {
  locale.value = lang
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <!-- Navbar -->
    <nav class="bg-white border-b border-gray-200">
      <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <router-link to="/" class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
          {{ t('home.title') }}
        </router-link>

        <div class="flex items-center gap-4">
          <!-- Navigation Links -->
          <template v-if="authStore.isAuthenticated">
            <router-link to="/submit">
              <el-button size="small" text>{{ t('nav.submit') }}</el-button>
            </router-link>
            <router-link to="/keys">
              <el-button size="small" text>{{ t('nav.api_keys') }}</el-button>
            </router-link>
            <router-link v-if="authStore.isAdmin" to="/admin">
              <el-button size="small" text>{{ t('nav.admin') }}</el-button>
            </router-link>
          </template>
          
          <!-- Lang Switcher -->
          <el-dropdown>
            <span class="el-dropdown-link cursor-pointer hover:text-blue-600">
              <span v-if="locale === 'en'">🇺🇸 English</span>
              <span v-else-if="locale === 'zh'">🇨🇳 中文</span>
              <span v-else-if="locale === 'fr'">🇫🇷 Français</span>
              <span v-else-if="locale === 'es'">🇪🇸 Español</span>
              <span v-else-if="locale === 'ar'">🇸🇦 العربية</span>
              <span v-else-if="locale === 'ru'">🇷🇺 Русский</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="switchLang('en')">🇺🇸 English</el-dropdown-item>
                <el-dropdown-item @click="switchLang('zh')">🇨🇳 中文</el-dropdown-item>
                <el-dropdown-item @click="switchLang('fr')">🇫🇷 Français</el-dropdown-item>
                <el-dropdown-item @click="switchLang('es')">🇪🇸 Español</el-dropdown-item>
                <el-dropdown-item @click="switchLang('ar')">🇸🇦 العربية</el-dropdown-item>
                <el-dropdown-item @click="switchLang('ru')">🇷🇺 Русский</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <!-- User Menu -->
          <template v-if="authStore.isAuthenticated">
            <span class="text-sm text-gray-500 hidden md:inline">{{ authStore.user?.email }}</span>
            <el-button size="small" @click="handleLogout">{{ t('nav.logout') }}</el-button>
          </template>
          <template v-else>
            <router-link to="/login">
              <el-button size="small" type="primary" plain>{{ t('nav.login') }}</el-button>
            </router-link>
            <router-link to="/register">
              <el-button size="small">{{ t('nav.register') }}</el-button>
            </router-link>
          </template>
        </div>
      </div>
    </nav>

    <div class="py-6">
       <router-view></router-view>
    </div>
  </div>
</template>
