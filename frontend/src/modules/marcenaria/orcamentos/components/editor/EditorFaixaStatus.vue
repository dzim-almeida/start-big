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

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { formatData, formatDataPura } from '@/shared/utils/date.utils';

import type { OrcamentoDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import { diasAteValidade } from '../../utils/validade';

const props = defineProps<{
  detalhe: OrcamentoDetalhe;
  /** Versão que substituiu esta (status SUBSTITUIDO), para o link "Abrir v3". */
  versaoSubstituta?: { id: number; versao: number } | null;
}>();

const emit = defineEmits<{
  voltarAEditar: [];
  recusar: [];
  novaVersao: [];
  renovar: [];
  abrirVersao: [id: number];
}>();

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
    case 'APROVADO':
      return `Aprovado em ${formatData(datas.aprovacao)}.`;
    default:
      return '';
  }
});

const acoes = computed(() => props.detalhe.acoes);

/** Cor da faixa: vencido e recusado chamam mais atenção. */
const classes = computed(() => {
  switch (props.detalhe.status) {
    case 'VENCIDO':
      return 'border-amber-200 bg-amber-50 text-amber-900';
    case 'RECUSADO':
      return 'border-red-200 bg-red-50 text-red-900';
    case 'APROVADO':
      return 'border-emerald-200 bg-emerald-50 text-emerald-900';
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
      <!-- A Spec 08B acrescenta aqui a OS do orçamento aprovado. -->
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
