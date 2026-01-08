/* eslint-env node */
require('@rushstack/eslint-patch/modern-module-resolution')

module.exports = {
  root: true,
  'extends': ['plugin:vue/vue3-essential', 'eslint:recommended', '@vue/eslint-config-typescript', '@vue/eslint-config-prettier/skip-formatting', 'plugin:storybook/recommended'],
  parserOptions: {
    ecmaVersion: 'latest'
  },
  rules: {
    // Regras personalizadas (opcional)
    
    // Permite nomes simples para componentes (ex: 'Login.vue' em vez de 'LoginPage.vue')
    'vue/multi-word-component-names': 'off', 
    
    // Evita erro se você usar 'any' no TypeScript (útil durante migrações, mas evite usar)
    '@typescript-eslint/no-explicit-any': 'warn'
  }
}