// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/eslint", "@nuxt/ui"],
  // Runtime environment configuration
  runtimeConfig: {
    public: {
      apiBase: "http://localhost:8000",
    },
  },
});
