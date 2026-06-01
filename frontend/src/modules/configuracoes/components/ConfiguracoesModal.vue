<script setup lang="ts">
import { computed, watch } from 'vue'
import type { Component } from 'vue'
import {
  Settings,
  X,
  Tag,
  Package,
  ClipboardList,
  Users,
  Banknote,
  Plug,
  Printer,
  Monitor,
  HardDrive,
  Headphones,
} from 'lucide-vue-next'

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue'
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'

import { useConfiguracoesModal } from '../composables/useConfiguracoesModal'
import type { SecaoConfiguracao, SecaoId } from '../types/configuracoes.types'

import RegrasDeVendas from './sections/regras-de-vendas/components/RegrasDeVendas.vue'
import ProdutosEstoque from './sections/produtos-estoque/components/ProdutosEstoque.vue'
import OrdensDeServico from './sections/ordens-de-servico/components/OrdensDeServico.vue'
import ClientesCadastro from './sections/clientes-cadastro/components/ClientesCadastro.vue'
import FinanceiroTaxas from './sections/financeiro-taxas/components/FinanceiroTaxas.vue'
import IntegracoesAPIs from './sections/integracoes-apis/components/IntegracoesAPIs.vue'
import ImpressaoPeriferico from './sections/impressao/components/ImpressaoPeriferico.vue'
import FormatosExibicao from './sections/formatos-exibicao/components/FormatosExibicao.vue'
import BackupDados from './sections/backup-dados/components/BackupDados.vue'
import Suporte from './sections/suporte/components/Suporte.vue'

const props = defineProps<{ isOpen: boolean; secaoInicial?: SecaoId }>()
const emit = defineEmits<{ close: [] }>()

const { secaoAtiva, irPara } = useConfiguracoesModal()

watch(() => props.isOpen, (aberto) => {
  if (aberto) irPara(props.secaoInicial ?? 'regras-de-vendas')
})

const secoes: SecaoConfiguracao[] = [
  { id: 'regras-de-vendas',  label: 'Regras de Vendas',      icone: Tag },
  { id: 'produtos-estoque',  label: 'Produtos e Estoque',    icone: Package },
  { id: 'ordens-de-servico', label: 'Ordens de Serviço',     icone: ClipboardList },
  { id: 'clientes-cadastro', label: 'Clientes e Cadastro',   icone: Users },
  { id: 'financeiro-taxas',  label: 'Financeiro e Taxas',    icone: Banknote },
  { id: 'integracoes-apis',  label: 'Integrações e APIs',    icone: Plug },
  { id: 'impressao',         label: 'Impressão e Periféricos', icone: Printer },
  { id: 'formatos-exibicao', label: 'Formatos e Exibição',   icone: Monitor },
  { id: 'backup-dados',      label: 'Backup dos Dados',      icone: HardDrive },
  { id: 'suporte',           label: 'Suporte',               icone: Headphones },
]

const componenteMap: Record<SecaoId, Component> = {
  'regras-de-vendas':  RegrasDeVendas,
  'produtos-estoque':  ProdutosEstoque,
  'ordens-de-servico': OrdensDeServico,
  'clientes-cadastro': ClientesCadastro,
  'financeiro-taxas':  FinanceiroTaxas,
  'integracoes-apis':  IntegracoesAPIs,
  'impressao':         ImpressaoPeriferico,
  'formatos-exibicao': FormatosExibicao,
  'backup-dados':      BackupDados,
  'suporte':           Suporte,
}

const componenteAtivo = computed(() => componenteMap[secaoAtiva.value])
</script>

<template>
  <BaseModal :is-open="isOpen" size="xl" title="Configurações Gerais" @close="emit('close')">
    <template #header>
      <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-100 shrink-0">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 bg-zinc-100 rounded-lg flex items-center justify-center">
            <Settings :size="16" class="text-zinc-600" />
          </div>
          <div>
            <h2 class="text-sm font-bold text-zinc-900">Configurações Gerais</h2>
            <p class="text-[11px] text-zinc-400 leading-tight">Gerencie as configurações do sistema</p>
          </div>
        </div>
        <button
          type="button"
          class="p-1.5 text-zinc-400 hover:text-red-500 hover:bg-zinc-100 rounded-lg transition-colors cursor-pointer"
          @click="emit('close')"
        >
          <X :size="18" />
        </button>
      </div>
    </template>

    <!-- Layout sidebar + conteúdo -->
    <div class="-mx-6 -my-6 flex overflow-hidden" style="height: 560px">

      <!-- Sidebar -->
      <nav class="w-52 border-r border-zinc-100 py-2 flex flex-col overflow-y-auto shrink-0 no-scrollbar">
        <p class="text-[9px] font-bold text-zinc-400 uppercase tracking-widest px-4 mb-1.5">
          Painel do Sistema
        </p>

        <button
          v-for="secao in secoes"
          :key="secao.id"
          type="button"
          :class="[
            'w-full flex items-center gap-2.5 px-4 py-2 text-left transition-colors cursor-pointer',
            secao.id === 'suporte' ? 'mt-1 border-t border-zinc-100 pt-3' : '',
            secaoAtiva === secao.id
              ? 'bg-brand-primary/8 text-brand-primary'
              : 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-800',
          ]"
          @click="irPara(secao.id)"
        >
          <component
            :is="secao.icone"
            :size="14"
            :class="secaoAtiva === secao.id ? 'text-brand-primary' : 'text-zinc-400'"
          />
          <span class="text-xs font-medium truncate">{{ secao.label }}</span>
        </button>
      </nav>

      <!-- Área de conteúdo -->
      <div class="flex-1 overflow-y-auto p-6 no-scrollbar">
        <component :is="componenteAtivo" />
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="ghost" size="sm" @click="emit('close')">
          Cancelar
        </BaseButton>
        <BaseButton variant="primary" size="sm" disabled>
          Salvar Alterações
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>

<style scoped>
.no-scrollbar {
  scrollbar-width: none;
}
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
</style>
