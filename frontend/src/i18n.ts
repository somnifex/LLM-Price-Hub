import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zh from './locales/zh.json'
import fr from './locales/fr.json'
import es from './locales/es.json'
import ar from './locales/ar.json'
import ru from './locales/ru.json'

// Supported languages (UN working languages + Chinese)
const supportedLocales = ['en', 'zh', 'fr', 'es', 'ar', 'ru']

// Detect browser language and match to supported locales
function getDefaultLocale(): string {
    const browserLang = navigator.language || (navigator as any).userLanguage || 'en'
    // Extract primary language code (e.g., 'zh-CN' -> 'zh')
    const primaryLang = browserLang.split('-')[0].toLowerCase()

    // Check if browser language is supported
    if (supportedLocales.includes(primaryLang)) {
        return primaryLang
    }

    // Default to English if not supported
    return 'en'
}

const i18n = createI18n({
    legacy: false, // Use Composition API
    locale: getDefaultLocale(),
    fallbackLocale: 'en',
    messages: {
        en,
        zh,
        fr,
        es,
        ar,
        ru
    }
})

export default i18n
