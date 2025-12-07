<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'

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

const getCurrentLangFlag = (lang: string) => {
  const flags: Record<string, string> = {
    en: '🇺🇸',
    zh: '🇨🇳',
    fr: '🇫🇷',
    es: '🇪🇸',
    ar: '🇸🇦',
    ru: '🇷🇺'
  }
  return flags[lang] || '🇺🇸'
}

const getCurrentLangName = (lang: string) => {
  const names: Record<string, string> = {
    en: 'English',
    zh: '中文',
    fr: 'Français',
    es: 'Español',
    ar: 'العربية',
    ru: 'Русский'
  }
  return names[lang] || 'English'
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 font-sans">
    <!-- Navbar -->
    <nav class="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100 transition-all duration-300">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2 group">
          <div class="w-8 h-8 bg-gradient-to-br from-primary-600 to-primary-800 rounded-lg flex items-center justify-center text-white font-bold shadow-lg group-hover:shadow-primary-500/30 transition-all duration-300">
            P
          </div>
          <span class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-700 group-hover:from-primary-600 group-hover:to-primary-800 transition-all duration-300">
            {{ t('home.title') }}
          </span>
        </router-link>

        <div class="flex items-center gap-6">
          <!-- Navigation Links -->
          <div v-if="authStore.isAuthenticated" class="hidden md:flex items-center gap-1 bg-gray-100/50 p-1 rounded-full border border-gray-200/50">
            <router-link to="/submit" custom v-slot="{ navigate, isActive }">
              <button @click="navigate" :class="['px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200', isActive ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50']">
                {{ t('nav.submit') }}
              </button>
            </router-link>
            <router-link to="/keys" custom v-slot="{ navigate, isActive }">
              <button @click="navigate" :class="['px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200', isActive ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50']">
                {{ t('nav.api_keys') }}
              </button>
            </router-link>
            <router-link v-if="authStore.isAdmin" to="/admin" custom v-slot="{ navigate, isActive }">
              <button @click="navigate" :class="['px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200', isActive ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50']">
                {{ t('nav.admin') }}
              </button>
            </router-link>
          </div>
          
          <div class="flex items-center gap-3">
            <!-- Lang Switcher -->
            <el-dropdown trigger="click">
              <button class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors text-sm font-medium text-gray-700 outline-none">
                <span>{{ getCurrentLangFlag(locale) }}</span>
                <span class="hidden sm:inline">{{ getCurrentLangName(locale) }}</span>
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu class="min-w-[120px]">
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
              <el-dropdown trigger="click">
                <div class="flex items-center gap-2 cursor-pointer pl-2 outline-none">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-r from-primary-100 to-primary-200 flex items-center justify-center text-primary-700 font-semibold border border-primary-200">
                    {{ authStore.user?.email?.[0]?.toUpperCase() || 'U' }}
                  </div>
                </div>
                <template #dropdown>
                  <el-dropdown-menu>
                    <div class="px-4 py-2 border-b border-gray-100 mb-1">
                      <p class="text-xs text-gray-500">Signed in as</p>
                      <p class="text-sm font-medium text-gray-900 truncate max-w-[150px]">{{ authStore.user?.email }}</p>
                    </div>
                    <el-dropdown-item @click="handleLogout" class="text-red-600">
                      {{ t('nav.logout') }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
            <template v-else>
              <div class="flex items-center gap-2">
                <el-button type="primary" class="!rounded-lg !px-5 !font-medium" @click="$router.push('/login')">
                  {{ t('nav.login') }}
                </el-button>
                <el-button class="!rounded-lg !px-5 hidden sm:block" @click="$router.push('/register')">
                  {{ t('nav.register') }}
                </el-button>
              </div>
            </template>
          </div>
        </div>
      </div>
    </nav>

    <div class="pb-12">
       <router-view></router-view>
    </div>
  </div>
</template>
