# Especificação Técnica: Frontend — Interface de Alerta e Confirmação de Numeração Fiscal

## 1. Metadados da Tarefa
- **Identificador / Branch:** `feat(fiscal-frontend): modal e badges de confirmacao da numeracao fiscal`
- **Camada:** Frontend (`Vue 3` / `<script setup>` / `TypeScript` / `Pinia` / `Tailwind CSS`)
- **Severidade:** Média/Alta (UX preventiva e alinhamento direto com o locker do backend)

---

## 2. Objetivo e Justificativa
Informar visualmente ao lojista e ao técnico de implantação que a sequência numérica e série fiscal precisam de confirmação formal antes da primeira emissão. 

A interface deve oferecer orientações didáticas sobre o preenchimento para dois cenários fundamentais:
1. **Empresa Nova:** Que nunca emitiu notas (inicia em Série 1, Último Número 0 para emitir a Nota 1).
2. **Empresa Vinda de Outro ERP:** Que já emitia notas (deve replicar a última numeração para não colidir na SEFAZ gerando a Rejeição 204).

Ao salvar as configurações, o frontend envia a confirmação formal para destravar as emissões no backend.

---

## 3. Detalhamento Técnico da Implementação

### 3.1. Tipagem TypeScript
- **Arquivo:** `frontend/src/modules/fiscal/types/fiscal.types.ts`
- **Alterações:**
  - Na interface `FiscalConfiguracao`:
    ```typescript
    export interface FiscalConfiguracao {
      // ... campos existentes
      numeracao_confirmada: boolean;
    }
    ```
  - Na interface/type `FiscalConfiguracaoUpdate`:
    ```typescript
    export interface FiscalConfiguracaoUpdate {
      // ... campos existentes
      numeracao_confirmada?: boolean;
    }
    ```

---

### 3.2. Modal de Emissão Estadual
- **Arquivo:** `frontend/src/modules/fiscal/components/configuracoes/FiscalEmissaoEstadualModal.vue`
- **Implementação:**
  1. **Envio Explícito da Flag:**
     - No método de submissão do formulário (`handleSave` / `onSubmit`), garantir que o payload da mutation inclua explicitamente:
       ```typescript
       numeracao_confirmada: true
       ```
  2. **Banner Informativo de Migração:**
     - Inserir um callout/card visual informativo logo acima dos campos de entrada de NF-e e NFC-e.
     - **Estilo:** Fundo azul ou neutro suave (`bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800/50 rounded-lg p-3 text-xs`).
     - **Conteúdo textual:**
       - **Empresa Nova:** Mantenha Série `1` e Último Número `0`. A 1ª nota emitida será a número 1.
       - **Migrando de outro sistema:** Informe a mesma série e o último número emitido no software anterior para evitar rejeição por duplicidade na SEFAZ.
  3. **Tag de Confirmação no Cabeçalho:**
     - Ao lado do título ou no topo do modal, se `configuracao.numeracao_confirmada === true`, renderizar um badge discreto:
       ```html
       <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
         <CheckIcon class="w-3 h-3" /> Sequência Confirmada
       </span>
       ```

---

### 3.3. Painel de Configurações Fiscais
- **Arquivo:** `frontend/src/modules/fiscal/views/FiscalConfiguracoesView.vue`
- **Implementação no Card "Emissão Estadual (SEFAZ)":**
  - **Estado Pendente (`config?.numeracao_confirmada === false`):**
    - Exibir badge com tom de alerta (amarelo/âmbar):
      `Ação necessária: confirme a numeração`
    - Mudar o texto do botão principal de ação do card para:
      `Confirmar Numeração`
  - **Estado Confirmado (`config?.numeracao_confirmada === true`):**
    - Exibir badge com tom de sucesso (verde):
      `Configurado e Confirmado`
    - Manter botão de ação padrão: `Configurar` ou `Editar`.

---

### 3.4. Guarda no Fluxo de Emissão (PDV e Vendas)
- **Arquivo:** `frontend/src/shared/composables/useEmitirFiscal.ts` (ou composable de emissão ativo):
- **Implementação:**
  - Antes de executar a chamada de emissão (manual, contingência ou teste):
    ```typescript
    if (fiscalConfig.value && !fiscalConfig.value.numeracao_confirmada) {
      toast.warning(
        'Confirme a série e o último número fiscal antes de realizar a primeira emissão.',
        {
          action: {
            label: 'Configurar',
            onClick: () => router.push({ name: 'fiscal-configuracoes' })
          }
        }
      );
      return false;
    }
    ```
  - Evita roundtrips desnecessários contra o backend e apresenta feedback contextual com atalho direto de resolução.

---

## 4. Critérios de Aceite e Testabilidade

1. **Visibilidade Imediata no Onboarding:**
   - Em instalações limpas ou com `numeracao_confirmada: false`, o painel fiscal deve destacar claramente o badge de ação necessária.
2. **Envio da Confirmação:**
   - Ao salvar o formulário no modal `FiscalEmissaoEstadualModal`, o payload HTTP `PUT` deve conter `"numeracao_confirmada": true`.
3. **Reatividade e Invalidação de Cache:**
   - Após o salvamento com sucesso, o modal fecha e o card de Emissão Estadual atualiza de imediato o badge para "Configurado e Confirmado" sem necessidade de refresh manual (`F5`).
4. **Intercepção no PDV/Vendas:**
   - Tentativas de emissão antes da confirmação devem exibir toast com link/redirecionamento, sem disparar a requisição de emissão para a API.
5. **Aderência ao Design System:**
   - Utilização das classes utilitárias do Tailwind CSS respeitando o modo claro/escuro (`dark:`) e sem estilos arbitrários desalinhados.

---

# Prompt
"
Você é um desenvolvedor frontend sênior especialista em Vue 3 (Composition API, `<script setup>`), TypeScript e Tailwind CSS.

Implemente a especificação de interface abaixo à risca, respeitando rigorosamente os caminhos de arquivos indicados, convenções de tipagem e a reatividade do sistema.

---

### TAREFA
feat(fiscal-frontend): modal e badges de confirmacao da numeracao fiscal

### CONTEXTO E OBJETIVO
Alertar visualmente o operador/implantador sobre a necessidade de confirmar a sequência de numeração e série fiscal antes da primeira emissão, oferecendo instruções claras (empresa nova vs migração de ERP) e acionando o destravamento no backend.

---

### DETALHAMENTO DA IMPLEMENTAÇÃO

1. Tipagem TypeScript
- Arquivo: `frontend/src/modules/fiscal/types/fiscal.types.ts`
  - Na interface `FiscalConfiguracao`: adicionar `numeracao_confirmada: boolean;`
  - Na interface/type `FiscalConfiguracaoUpdate`: adicionar `numeracao_confirmada?: boolean;`

2. Modal de Configuração Estadual
- Arquivo: `frontend/src/modules/fiscal/components/configuracoes/FiscalEmissaoEstadualModal.vue`
  - No método de submissão (`handleSave`):
    Garantir o envio explícito de `numeracao_confirmada: true` no payload da mutation `salvarConfig`.
  - Inserir banner visual de orientação (card com fundo neutro/azul sutil) posicionado logo acima dos inputs de NF-e e NFC-e:
    - **Nova Empresa:** Instruir a manter Série 1 e Último Número 0 (a primeira nota emitida será a número 1).
    - **Empresa em Migração:** Instruir a preencher a mesma série e o último número emitido no ERP anterior para evitar a Rejeição SEFAZ 204.
  - No cabeçalho do modal: caso `configuracao.numeracao_confirmada` seja `true`, exibir uma tag discreta "Sequência Confirmada".

3. Painel de Configurações Fiscais
- Arquivo: `frontend/src/modules/fiscal/views/FiscalConfiguracoesView.vue`
  - No card referente a "Emissão Estadual (SEFAZ)":
    - Se `config?.numeracao_confirmada === false`:
      - Exibir badge chamativo (amarelo/laranja): `Ação necessária: confirme a numeração`.
      - Alterar o texto do CTA para `Confirmar Numeração`.
    - Se `config?.numeracao_confirmada === true`:
      - Exibir badge de status verde: `Configurado e Confirmado`.

4. Guarda Preventiva na Emissão
- Arquivo: `frontend/src/shared/composables/useEmitirFiscal.ts` (ou composable de emissão ativo):
  - Interceptar tentativas de emissão quando `numeracao_confirmada === false`.
  - Exibir toast/alerta orientativo guiando o usuário para a tela de configurações antes de disparar a requisição ao servidor.

---

### RESTRIÇÕES E CRITÉRIOS
- Tipagem 100% estrita em TypeScript (sem uso de `any`).
- Preservar o padrão de `<script setup lang="ts">`.
- Invalidação de query/cache reativa após a mutation para atualização em tempo real do painel.
"
---

## Desvios aplicados na implementação (2026-09-17)
Ver `.agent/docs/progress/TASK001-FRONTEND.md`. Resumo:
- Chips no padrão dos chips existentes do sistema (rounded-full, amber-700/emerald-700), sem `dark:` (o app não tem tema escuro).
- Guarda aplicada também nos modais do Centro Fiscal (manual, lote, teste), não só em `useEmitirFiscal`.
- `FiscalConfiguracaoUpdate` criado como interface própria; `as any` do modal removido.
- Testes: Vitest instalado (`npm run test`); `composables/__tests__/useNumeracaoConfirmada.spec.ts`.
