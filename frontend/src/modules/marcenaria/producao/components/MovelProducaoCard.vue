<script setup lang="ts">
/**
 * @component MovelProducaoCard
 * @description Um móvel na aba Produção (Spec 12B D3, D7, D8).
 *
 * - Feito na fábrica: as etapas como chips, em linha, na ordem do móvel.
 * - Terceirizado: sem chips; mostra a situação da 11B ("Pedido enviado ·
 *   chega 20/10") e fica verde "Pronto" quando conferido (E6a).
 * - Sem etapas (12A D6): o aviso e "Aplicar etapas padrão".
 * - Menu "⋯" do cartão: "Editar etapas" e "Imprimir etiquetas" (Spec 14 D8, D9:
 *   o terceirizado também pode ter etiqueta).
 *
 * Só desenha e avisa o pai: quem grava é a aba.
 */
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { AlertTriangle, CheckCircle2, MoreHorizontal } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { ROTULO_SITUACAO, textoDasMedidas } from '@/modules/marcenaria/terceirizados/utils/terceirizados';

import type { Etapa, MovelProducao } from '../schemas/producao.schema';
import { diaMes, etapasEmOrdem, proximaEtapa } from '../utils/producao';
import EtapaChip from './EtapaChip.vue';

const props = defineProps<{
  movel: MovelProducao;
  editavel: boolean;
  modoSelecao: boolean;
  /** Os ids das etapas marcadas no modo seleção (de todos os móveis). */
  selecionadas: Set<number>;
}>();

const emit = defineEmits<{
  concluir: [etapa: Etapa];
  iniciar: [etapa: Etapa];
  reabrir: [etapa: Etapa];
  alternar: [etapa: Etapa];
  editarEtapas: [];
  aplicarPadrao: [];
  /** Spec 14 D8: as etiquetas só deste móvel. */
  imprimirEtiquetas: [];
}>();

const terceirizado = computed(() => props.movel.terceirizado ?? null);
const etapas = computed(() => etapasEmOrdem(props.movel));
const proxima = computed(() => proximaEtapa(props.movel));
const medidas = computed(() => textoDasMedidas(props.movel));

/** D7: "Pedido enviado · chega 20/10" (a previsão só enquanto está a caminho). */
/** "Editar etapas": só no móvel feito na fábrica, com etapas e a OS aberta. */
const podeEditarEtapas = computed(() => props.editavel && !terceirizado.value && !props.movel.sem_etapas);

const textoTerceirizado = computed(() => {
  const t = terceirizado.value;
  if (!t) return '';
  const chega = t.situacao === 'ENVIADO' && t.previsao ? ` · chega ${diaMes(t.previsao)}` : '';
  return `Central · ${ROTULO_SITUACAO[t.situacao]}${chega}`;
});

// --- Menu "⋯" do cartão (D8) -----------------------------------------------------------
const menuAberto = ref(false);
const menuRef = ref<HTMLElement | null>(null);
onClickOutside(menuRef, () => { menuAberto.value = false; });
</script>

<template>
  <div
    class="rounded-xl border px-4 py-3"
    :class="movel.pronto ? 'border-emerald-200 bg-emerald-50/40' : 'border-zinc-200 bg-white'"
    :data-testid="`movel-${movel.movel_id}`"
  >
    <div class="flex flex-wrap items-start justify-between gap-2">
      <p class="text-sm font-semibold text-zinc-900">
        {{ movel.nome }}
        <span class="ml-1 text-xs font-normal text-zinc-500">
          <template v-if="medidas">{{ medidas }} · </template>{{ movel.quantidade }}×
        </span>
        <span v-if="movel.pronto" class="ml-2 inline-flex items-center gap-1 text-xs font-semibold text-emerald-700" data-testid="pronto">
          <CheckCircle2 :size="14" /> Pronto
        </span>
      </p>

      <!-- Menu do cartão: etiquetas sempre; editar etapas só no móvel da fábrica com a OS aberta -->
      <div ref="menuRef" class="relative">
        <BaseButton
          variant="secondary"
          size="sm"
          aria-haspopup="menu"
          :aria-expanded="menuAberto"
          aria-label="Mais ações do móvel"
          :data-testid="`menu-movel-${movel.movel_id}`"
          @click="menuAberto = !menuAberto"
        >
          <MoreHorizontal :size="16" />
        </BaseButton>
        <div v-if="menuAberto" role="menu" class="absolute right-0 z-30 mt-1 w-44 overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-lg">
          <button
            v-if="podeEditarEtapas"
            type="button"
            role="menuitem"
            class="block w-full px-3 py-2 text-left text-sm text-zinc-700 hover:bg-zinc-50 cursor-pointer"
            data-testid="opcao-editar-etapas"
            @click="menuAberto = false; emit('editarEtapas')"
          >
            Editar etapas
          </button>
          <button
            type="button"
            role="menuitem"
            class="block w-full px-3 py-2 text-left text-sm text-zinc-700 hover:bg-zinc-50 cursor-pointer"
            data-testid="opcao-imprimir-etiquetas"
            @click="menuAberto = false; emit('imprimirEtiquetas')"
          >
            Imprimir etiquetas
          </button>
        </div>
      </div>
    </div>

    <!-- D7: terceirizado, a situação da central -->
    <p v-if="terceirizado" class="mt-2 flex flex-wrap items-center gap-2 text-sm text-zinc-600" data-testid="situacao-terceirizado">
      {{ textoTerceirizado }}
      <span v-if="terceirizado.atrasado" class="inline-flex items-center gap-1 text-xs font-semibold text-red-700">
        <AlertTriangle :size="12" /> Atrasado
      </span>
    </p>

    <!-- D8 / 12A D6: sem etapas, sem caminho para ficar pronto -->
    <div v-else-if="movel.sem_etapas" class="mt-2 flex flex-wrap items-center gap-3" data-testid="sem-etapas">
      <p class="text-sm text-amber-800">Este móvel não tem etapas de produção.</p>
      <BaseButton v-if="editavel" size="sm" variant="secondary" data-testid="aplicar-padrao" @click="emit('aplicarPadrao')">
        Aplicar etapas padrão
      </BaseButton>
    </div>

    <!-- D3: os chips, na ordem do móvel -->
    <div v-else class="mt-2 flex flex-wrap gap-2">
      <EtapaChip
        v-for="etapa in etapas"
        :key="etapa.id"
        :etapa="etapa"
        :proxima="proxima?.id === etapa.id"
        :editavel="editavel"
        :modo-selecao="modoSelecao"
        :selecionada="selecionadas.has(etapa.id)"
        @concluir="emit('concluir', etapa)"
        @iniciar="emit('iniciar', etapa)"
        @reabrir="emit('reabrir', etapa)"
        @alternar="emit('alternar', etapa)"
      />
    </div>
  </div>
</template>
