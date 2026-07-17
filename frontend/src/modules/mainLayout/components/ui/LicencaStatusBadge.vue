<script setup lang="ts">
/**
 * @component LicencaStatusBadge
 * @description Badge no header que exibe o status da licença/trial com visual dinâmico.
 * Sempre visível quando o status está disponível; silencioso em erros de rede.
 *
 * Estados:
 *  - trial:           trial ativo, dias > 7  → azul/brand
 *  - trial-urgente:   trial ativo, dias ≤ 7  → laranja pulsante
 *  - renovar:         licença paga, dias ≤ 30 → amarelo
 *  - renovar-urgente: licença paga, dias ≤ 7  → vermelho pulsante
 *  - ativo:           licença saudável        → verde/neutro (sem CTA)
 */

import { computed } from 'vue';
import { Zap, AlertTriangle, Clock } from 'lucide-vue-next';
import { openUrl } from '@tauri-apps/plugin-opener';
import { useLicencaStatusQuery } from '@/shared/composables/useLicencaStatusQuery';

const URL_COMPRA = 'https://api.startbig.com.br/comprar-placeholder';

const { data, isLoading, isError } = useLicencaStatusQuery();

type BadgeEstado = 'trial' | 'trial-urgente' | 'renovar' | 'renovar-urgente' | 'ativo';

const estado = computed((): BadgeEstado | null => {
  if (isLoading.value || isError.value || !data.value) return null;

  const { trial, dias_restantes } = data.value;
  const dias = dias_restantes ?? Infinity;

  if (trial) {
    return dias <= 7 ? 'trial-urgente' : 'trial';
  }
  if (dias <= 7) return 'renovar-urgente';
  if (dias <= 30) return 'renovar';
  return 'ativo';
});

const config = computed(() => {
  const dias = data.value?.dias_restantes;

  switch (estado.value) {
    case 'trial':
      return {
        label: `Trial • ${dias} dias`,
        icon: Zap,
        classes: 'bg-brand-primary/10 text-brand-primary hover:bg-brand-primary/20',
        showCta: true,
      };
    case 'trial-urgente':
      return {
        label: `Trial • ${dias} dias`,
        icon: Clock,
        classes: 'bg-orange-50 text-orange-600 hover:bg-orange-100 animate-pulse',
        showCta: true,
      };
    case 'renovar':
      return {
        label: `Renovar • ${dias} dias`,
        icon: AlertTriangle,
        classes: 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100',
        showCta: true,
      };
    case 'renovar-urgente':
      return {
        label: `Renovar • ${dias} dias`,
        icon: AlertTriangle,
        classes: 'bg-red-50 text-red-600 hover:bg-red-100 animate-pulse',
        showCta: true,
      };
    case 'ativo':
      return {
        label: 'Assinatura Ativa',
        icon: Zap,
        classes: 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100',
        showCta: false,
      };
    default:
      return null;
  }
});

function handleClick() {
  if (config.value?.showCta) {
    openUrl(URL_COMPRA);
  }
}
</script>

<template>
  <button
    v-if="config"
    type="button"
    class="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-colors"
    :class="[config.classes, config.showCta ? 'cursor-pointer' : 'cursor-default']"
    :title="config.showCta ? 'Clique para fazer upgrade' : 'Licença ativa'"
    @click="handleClick"
  >
    <component :is="config.icon" :size="13" />
    <span class="hidden md:inline">{{ config.label }}</span>
  </button>
</template>
