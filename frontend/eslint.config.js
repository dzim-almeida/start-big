// ESLint 9 (flat config). Substitui o `.eslintrc.cjs`, que o ESLint 9 e o
// eslint-plugin-vue 10 não leem mais: de 10/2026 até a migração (G8 do
// backend-fastapi/docs/nfse-fase2-plano.md) o `npm run lint` não rodava, e a
// regra da marcenaria abaixo não era aplicada.
//
// Mesmas regras de antes, menos o `plugin:storybook/recommended`: o
// eslint-plugin-storybook nunca foi instalado.
import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default defineConfigWithVueTs(
  {
    name: 'app/arquivos',
    files: ['**/*.{ts,mts,tsx,vue,js,jsx,cjs,mjs}'],
  },
  {
    name: 'app/ignorados',
    ignores: ['dist/**', 'build/**', 'dist-ssr/**', 'coverage/**', 'storybook-static/**', 'src-tauri/**', 'public/**'],
  },

  js.configs.recommended,
  pluginVue.configs['flat/essential'],
  vueTsConfigs.recommended,
  skipFormatting,

  {
    name: 'app/regras',
    rules: {
      // Permite nomes simples para componentes (ex: 'Login.vue' em vez de 'LoginPage.vue')
      'vue/multi-word-component-names': 'off',
      // Evita erro se você usar 'any' no TypeScript (útil durante migrações, mas evite usar)
      '@typescript-eslint/no-explicit-any': 'warn',
      // `_nome` é "não usado de propósito" (assinatura de callback, valor
      // descartado), e o `catch (error)` sem uso é o jeito da casa de engolir.
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrors: 'none',
      }],
      // `interface CargoCreate extends CargoBase {}` nomeia um contrato da API.
      '@typescript-eslint/no-empty-object-type': ['error', { allowInterfaces: 'with-single-extends' }],
      // O timer de reserva da impressão é lido dentro do `limpar` antes de ser
      // atribuído (o `limpar` só roda depois): `let` aí é de propósito.
      'prefer-const': ['error', { ignoreReadBeforeAssign: true }],
    },
  },

  {
    // Declarações de tipo (o `DefineComponent<{}, {}, any>` do vite-env é o
    // modelo oficial do Vite).
    name: 'app/declaracoes',
    files: ['**/*.d.ts'],
    rules: { '@typescript-eslint/no-empty-object-type': 'off' },
  },

  {
    // Marcenaria (redesign 10/2026): campo de formulário é componente base,
    // para o módulo não voltar a sair do padrão visual do sistema. Exceção
    // precisa de motivo escrito: `<!-- eslint-disable-next-line ... -- motivo -->`.
    name: 'app/marcenaria',
    files: ['src/modules/marcenaria/**/*.vue'],
    ignores: ['**/__tests__/**', '**/*Print*.vue'],
    rules: {
      'vue/no-restricted-html-elements': ['error',
        { element: 'select', message: 'Use o BaseSelect (shared/components/ui).' },
        { element: 'textarea', message: 'Use o BaseTextarea (shared/components/ui).' },
      ],
    },
  },
)
