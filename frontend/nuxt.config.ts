export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  app: {
    head: {
      title: 'PranataCRM',
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'shortcut icon', href: '/favicon.svg' },
      ],
    },
  },

  modules: [
    '@nuxt/ui',
    '@pinia/nuxt',
    '@nuxtjs/i18n',
  ],

  ui: {
    global: true,
  },

  i18n: {
    locales: [
      { code: 'id', file: 'id.json', name: 'Indonesia' },
      { code: 'en', file: 'en.json', name: 'English' },
    ],
    defaultLocale: 'id',
    strategy: 'no_prefix',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_redirected',
      redirectOn: 'root',
    },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8230/api/v1',
      appEnv: process.env.NUXT_PUBLIC_APP_ENV || 'development',
    },
  },

  routeRules: {
    '/app/**': { ssr: false },
  },

  css: ['~/assets/css/main.css'],
})
