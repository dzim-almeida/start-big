<script setup lang="ts">
import { computed, ref, watch } from 'vue'
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
  ShieldCheck,
} from 'lucide-vue-next'

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue'
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'
import GerenteAprovacaoModal from '@/shared/components/commons/GerenteAprovacaoModal/GerenteAprovacaoModal.vue'

import { useConfiguracoesModal } from '../composables/useConfiguracoesModal'
import { useSalvarConfiguracoesClientesMutation } from '../composables/mutates/useSalvarConfiguracoesClientesMutation'
import { useSalvarConfiguracoesEstoqueMutation } from '../composables/mutates/useSalvarConfiguracoesEstoqueMutation'
import { useSalvarConfiguracoesOSMutation } from '../composables/mutates/useSalvarConfiguracoesOSMutation'
import { useSalvarConfiguracoesVendasMutation } from '../composables/mutates/useSalvarConfiguracoesVendasMutation'
import { useSalvarConfiguracoesSegurancaMutation } from '../composables/mutates/useSalvarConfiguracoesSegurancaMutation'
import type { SecaoConfiguracao, SecaoId } from '../types/configuracoes.types'
import { useGerenteAprovacao } from '@/shared/composables/useGerenteAprovacao'
import { verificarPinSeguranca } from '../services/configuracoes.service'
import { useToast } from '@/shared/composables/useToast'
import { storeToRefs } from 'pinia'
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store'

import RegrasDeVendas from './sections/regras-de-vendas/components/RegrasDeVendas.vue'
import Seguranca from './sections/seguranca/components/Seguranca.vue'
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
const { mutate: salvarClientes, isPending: isPendingClientes } = useSalvarConfiguracoesClientesMutation()
const { mutate: salvarEstoque, isPending: isPendingEstoque } = useSalvarConfiguracoesEstoqueMutation()
const { mutate: salvarOS, isPending: isPendingOS } = useSalvarConfiguracoesOSMutation()
const { mutate: salvarVendas, isPending: isPendingVendas } = useSalvarConfiguracoesVendasMutation()
const { mutate: salvarSeguranca, isPending: isPendingSeguranca } = useSalvarConfiguracoesSegurancaMutation()

const { requerPinAcessarConfigSensivel, temPinConfigurado } = storeToRefs(useConfiguracoesStore())
const gerenteConfig = useGerenteAprovacao()
const toast = useToast()

const SECOES_OUTRAS_SENSIVEIS: SecaoId[] = ['regras-de-vendas', 'financeiro-taxas']

function precisaPin(secaoId: SecaoId): boolean {
  if (secaoId === 'seguranca') return temPinConfigurado.value
  return requerPinAcessarConfigSensivel.value && SECOES_OUTRAS_SENSIVEIS.includes(secaoId)
}

async function verificarENavegar(secaoId: SecaoId, pin: string): Promise<void> {
  try {
    gerenteConfig.isLoading.value = true
    await verificarPinSeguranca(pin)
    irPara(secaoId)
  } catch (error: any) {
    const detail = error?.response?.data?.detail
    if (detail === 'PIN_GERENTE_INVALIDO') {
      toast.error('PIN do gerente inválido. Tente novamente.')
      const novoPIN = await gerenteConfig.pedirPin()
      if (novoPIN) await verificarENavegar(secaoId, novoPIN)
    }
  } finally {
    gerenteConfig.isLoading.value = false
  }
}

async function navegarParaSecao(secaoId: SecaoId): Promise<void> {
  if (!precisaPin(secaoId)) {
    irPara(secaoId)
    return
  }
  const pin = await gerenteConfig.pedirPin()
  if (!pin) return
  await verificarENavegar(secaoId, pin)
}

const isPending = computed(() => isPendingClientes.value || isPendingEstoque.value || isPendingOS.value || isPendingVendas.value || isPendingSeguranca.value)

const activeComponentRef = ref<{ form?: Record<string, unknown> } | null>(null)

watch(() => props.isOpen, (aberto) => {
  if (aberto) irPara(props.secaoInicial ?? 'regras-de-vendas')
})

const secoesFuncionais: SecaoId[] = ['seguranca', 'clientes-cadastro', 'produtos-estoque', 'ordens-de-servico', 'regras-de-vendas']
const secaoFuncional = computed(() => secoesFuncionais.includes(secaoAtiva.value))

function salvar() {
  if (secaoAtiva.value === 'clientes-cadastro' && activeComponentRef.value?.form) {
    salvarClientes(activeComponentRef.value.form as any)
  }
  if (secaoAtiva.value === 'produtos-estoque' && activeComponentRef.value?.form) {
    salvarEstoque(activeComponentRef.value.form as any)
  }
  if (secaoAtiva.value === 'ordens-de-servico' && activeComponentRef.value?.form) {
    salvarOS(activeComponentRef.value.form as any)
  }
  if (secaoAtiva.value === 'regras-de-vendas' && activeComponentRef.value?.form) {
    const { vendas, estoque } = activeComponentRef.value.form as { vendas: Record<string, unknown>; estoque: Record<string, unknown> }
    salvarVendas(vendas as any)
    salvarEstoque(estoque as any)
  }
  if (secaoAtiva.value === 'seguranca' && activeComponentRef.value?.form) {
    salvarSeguranca(activeComponentRef.value.form as any)
  }
}

const secoes: SecaoConfiguracao[] = [
  { id: 'seguranca',         label: 'Segurança',             icone: ShieldCheck },
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
  'seguranca':         Seguranca,
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
  <GerenteAprovacaoModal
    :is-open="gerenteConfig.isOpen.value"
    :is-loading="gerenteConfig.isLoading.value"
    @confirmar="gerenteConfig.confirmar"
    @cancelar="gerenteConfig.cancelar"
  />
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
          @click="navegarParaSecao(secao.id)"
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
        <component
          :is="componenteAtivo"
          ref="activeComponentRef"
        />
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="ghost" size="sm" :disabled="isPending" @click="emit('close')">
          Cancelar
        </BaseButton>
        <BaseButton variant="primary" size="sm" :isLoading="isPending" :disabled="!secaoFuncional || isPending" @click="salvar">
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
