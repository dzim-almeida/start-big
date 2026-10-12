<script setup lang="ts">
/**
 * @component EditorFaixaStatus
 * @description Faixa do topo do editor fora do rascunho (Spec 06B D13, §6.3).
 *
 * Responde "por que não consigo editar?" antes de a pergunta surgir e oferece
 * a ação certa. Cada botão aparece SÓ se a ação correspondente de `acoes`
 * vier `true` (a regra é do backend).
 */
import { computed } from 'vue';
import { Info } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatData, formatDataPura } from '@/shared/utils/date.utils';
import { formatCurrency } from '@/shared/utils/finance';

import type { OrcamentoDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import { diasAteValidade } from '../../utils/validade';

const props = defineProps<{
  detalhe: OrcamentoDetalhe;
  /** Versão que substituiu esta (status SUBSTITUIDO), para o link "Abrir v3". */
  versaoSubstituta?: { id: number; versao: number } | null;
  /** Aprovado (08B D12): quem aprovou, vindo do resumo da OS. */
  aprovadoPor?: string | null;
  /** Aprovado: o status da OS no texto do segmento ("Aberta", "Em Produção"). */
  rotuloStatusOs?: string | null;
  /** Aprovado sem poder desfazer: os motivos, para o ícone de informação (D18). */
  motivosDesfazer?: string[];
  /**
   * Spec 09B D10: a loja tem o módulo Financeiro? Só então a linha do RT ganha
   * o link "Ver em Contas a Pagar" (sem o módulo, a tela nem abre).
   */
  temFinanceiro?: boolean;
}>();

const emit = defineEmits<{
  voltarAEditar: [];
  recusar: [];
  novaVersao: [];
  renovar: [];
  abrirVersao: [id: number];
  /** Aprovado (08B D12): abrir a OS, imprimir a proposta aprovada, desfazer. */
  abrirOs: [];
  propostaAprovada: [];
  desfazer: [];
  /** Spec 09B D10: abrir Contas a Pagar (quem navega é o editor). */
  contasPagar: [];
}>();

/** A OS do orçamento aprovado foi cancelada pela tela de OS (08A D21, 08B D15). */
const osCancelada = computed(() => props.detalhe.status === 'APROVADO' && props.detalhe.os?.status === 'CANCELADA');

/** "(em 15 dias)" / "(vence amanhã)" / "(vence hoje)". */
function prazoRestante(validade: string): string {
  const dias = diasAteValidade(validade);
  if (dias > 1) return `(em ${dias} dias)`;
  if (dias === 1) return '(vence amanhã)';
  return '(vence hoje)';
}

/** O texto da faixa por status (§6.3). Rascunho não tem faixa. */
const texto = computed(() => {
  const { status, datas, motivo_recusa: motivo } = props.detalhe;
  switch (status) {
    case 'ENVIADO':
      return `Enviado em ${formatData(datas.envio)}.`
        + (datas.validade ? ` Vale até ${formatDataPura(datas.validade)} ${prazoRestante(datas.validade)}.` : '');
    case 'VENCIDO':
      return `A validade terminou em ${formatDataPura(datas.validade)}.`;
    case 'RECUSADO':
      // Motivo digitado com ponto final não vira "Preço..".
      return `Recusado em ${formatData(datas.recusa)}${motivo ? `: ${motivo.replace(/[.\s]+$/, '')}` : ''}.`;
    case 'SUBSTITUIDO':
      return props.versaoSubstituta
        ? `Esta versão foi substituída pela v${props.versaoSubstituta.versao}.`
        : 'Esta versão foi substituída por uma mais nova.';
    case 'APROVADO': {
      const os = props.detalhe.os;
      if (osCancelada.value && os) return `A OS ${os.numero_os} foi cancelada.`;
      // "Aprovado em 06/10/2026 por Alan · OS-2026-000512 (Aberta)" (08B D12).
      const quem = props.aprovadoPor ? ` por ${props.aprovadoPor}` : '';
      const daOs = os ? ` · ${os.numero_os}${props.rotuloStatusOs ? ` (${props.rotuloStatusOs})` : ''}` : '';
      return `Aprovado em ${formatData(datas.aprovacao)}${quem}${daOs}.`;
    }
    default:
      return '';
  }
});

const acoes = computed(() => props.detalhe.acoes);

/** Como a conta a pagar aparece para o usuário (os mesmos nomes de Contas a Pagar). */
const ROTULO_CONTA: Record<string, string> = { PENDENTE: 'Pendente', PAGA: 'Paga', CANCELADA: 'Cancelada' };

/**
 * Linha do RT no orçamento aprovado (Spec 09B D10, C5e): o dono vê se o
 * arquiteto já tem conta a pagar sem ir procurar. Só com custos (o valor do RT
 * é custo) e com arquiteto; com a OS cancelada, a faixa já diz o que importa.
 * - antes de finalizar a OS: "RT de Studio Renascer: previsto R$ 739,11 · conta criada na finalização da OS."
 * - depois: "RT de Studio Renascer: conta a pagar de R$ 739,11, vence 05/12/2026 (Pendente)."
 */
const linhaRt = computed(() => {
  const d = props.detalhe;
  if (d.status !== 'APROVADO' || osCancelada.value || !d.inclui_custos) return null;
  const arquiteto = d.arquitetos[0];                         // um arquiteto por orçamento na tela (C5a)
  if (!arquiteto) return null;
  const conta = arquiteto.conta;
  if (!conta) {
    return {
      texto: `RT de ${arquiteto.nome}: previsto ${formatCurrency(arquiteto.valor_previsto_centavos)} · conta criada na finalização da OS.`,
      temConta: false,
    };
  }
  const situacao = ROTULO_CONTA[conta.status] ?? conta.status;   // status novo do backend aparece cru, não some
  return {
    texto: `RT de ${arquiteto.nome}: conta a pagar de ${formatCurrency(conta.valor_centavos)}, vence ${formatDataPura(conta.vencimento)} (${situacao}).`,
    temConta: true,
  };
});

/** Cor da faixa: vencido e recusado chamam mais atenção. */
const classes = computed(() => {
  switch (props.detalhe.status) {
    case 'VENCIDO':
      return 'border-amber-200 bg-amber-50 text-amber-900';
    case 'RECUSADO':
      return 'border-red-200 bg-red-50 text-red-900';
    case 'APROVADO':
      return osCancelada.value ? 'border-red-200 bg-red-50 text-red-900' : 'border-emerald-200 bg-emerald-50 text-emerald-900';
    default:
      return 'border-blue-200 bg-blue-50 text-blue-900';
  }
});
</script>

<template>
  <div
    v-if="texto"
    class="flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm"
    :class="classes"
    data-testid="faixa-status"
  >
    <div>
      <p data-testid="faixa-texto">{{ texto }}</p>
      <!-- RT do arquiteto (09B D10): previsto ou a conta a pagar. -->
      <p v-if="linhaRt" class="mt-1 text-xs" data-testid="faixa-rt">
        {{ linhaRt.texto }}
        <!-- O link só existe com o Financeiro: sem o módulo, a tela de contas nem abre. -->
        <button
          v-if="linhaRt.temConta && temFinanceiro"
          type="button"
          class="ml-1 font-semibold underline cursor-pointer"
          data-testid="ver-contas-pagar"
          @click="emit('contasPagar')"
        >
          Ver em Contas a Pagar
        </button>
      </p>
      <slot />
    </div>
    <div class="flex flex-wrap gap-2">
      <BaseButton v-if="acoes.renovar" size="sm" variant="primary" data-testid="acao-renovar" @click="emit('renovar')">Renovar</BaseButton>
      <BaseButton v-if="acoes.voltar_a_editar" size="sm" variant="secondary" data-testid="acao-voltar" @click="emit('voltarAEditar')">
        Voltar a editar
      </BaseButton>
      <BaseButton v-if="acoes.recusar" size="sm" variant="secondary" data-testid="acao-recusar" @click="emit('recusar')">Recusar</BaseButton>
      <BaseButton v-if="acoes.nova_versao" size="sm" variant="secondary" data-testid="acao-nova-versao" @click="emit('novaVersao')">
        Nova versão
      </BaseButton>
      <!-- Aprovado (08B D12): os próximos passos; com a OS cancelada, só "Nova versão" (D15). -->
      <template v-if="detalhe.status === 'APROVADO' && detalhe.os && !osCancelada">
        <BaseButton size="sm" variant="primary" data-testid="acao-abrir-os" @click="emit('abrirOs')">Abrir OS</BaseButton>
        <BaseButton size="sm" variant="secondary" data-testid="acao-proposta-aprovada" @click="emit('propostaAprovada')">Proposta aprovada</BaseButton>
        <BaseButton v-if="acoes.desfazer_aprovacao" size="sm" variant="ghost-danger" data-testid="acao-desfazer" @click="emit('desfazer')">
          Desfazer aprovação
        </BaseButton>
        <!-- D18: sem poder desfazer, diz por quê (sem tentar e falhar). -->
        <span
          v-else-if="motivosDesfazer?.length"
          class="inline-flex items-center gap-1 text-xs text-emerald-900/70"
          :title="motivosDesfazer.join(' ')"
          data-testid="motivos-desfazer"
        >
          <Info :size="14" /> Não dá para desfazer
          <span class="sr-only">: {{ motivosDesfazer.join(' ') }}</span>
        </span>
      </template>
      <BaseButton
        v-if="detalhe.status === 'SUBSTITUIDO' && versaoSubstituta"
        size="sm"
        variant="secondary"
        data-testid="acao-abrir-versao"
        @click="emit('abrirVersao', versaoSubstituta.id)"
      >
        Abrir v{{ versaoSubstituta.versao }}
      </BaseButton>
    </div>
  </div>
</template>
