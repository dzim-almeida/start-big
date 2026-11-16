<script setup lang="ts">
/**
 * @component FranquiaFiscalCard
 * @description O saldo da franquia fiscal do mês, no cabeçalho das abas NF-e,
 * NFC-e e NFS-e (docs/nfse-fase2-plano.md, G1). Mesmo visual do botão "Saúde
 * Fiscal". Some quando a plataforma não informa (nada inventado).
 */
import { Gauge } from 'lucide-vue-next';

import { useFranquiaFiscal } from '../../composables/useFranquiaFiscal';

const { franquia, resumo, alerta, percentual } = useFranquiaFiscal();
</script>

<template>
  <div
    v-if="franquia"
    class="flex items-center gap-3 px-4 py-2 rounded-xl border bg-white"
    :class="alerta ? 'border-amber-300' : 'border-zinc-200'"
    :title="
      franquia.formaCobranca === 'PIX'
        ? 'Pagamento por PIX: a emissão para quando a franquia acabar.'
        : `Cartão: cada nota acima da franquia custa ${franquia.precoExcedente.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}, até ${franquia.limite} no mês.`
    "
    data-franquia-fiscal
  >
    <Gauge :size="16" :class="alerta ? 'text-amber-600' : 'text-brand-primary'" />
    <div class="flex flex-col items-start">
      <span class="text-xs font-semibold text-zinc-700 leading-none">Franquia do mês</span>
      <div class="flex items-center gap-2 mt-1">
        <div class="w-16 h-1.5 rounded-full bg-zinc-100 overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-700"
            :class="alerta ? 'bg-amber-400' : 'bg-brand-primary'"
            :style="{ width: percentual + '%' }"
          />
        </div>
        <span class="text-[10px] font-medium text-zinc-500 whitespace-nowrap">{{ resumo }}</span>
      </div>
    </div>
  </div>
</template>
