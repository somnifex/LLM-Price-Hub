const isProd = typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.MODE === 'production'

export default {
  error: (...args: any[]) => {
    if (!isProd) console.error(...args)
  },
  warn: (...args: any[]) => {
    if (!isProd) console.warn(...args)
  },
  info: (...args: any[]) => {
    if (!isProd) console.info(...args)
  },
  debug: (...args: any[]) => {
    if (!isProd) console.debug(...args)
  }
}
