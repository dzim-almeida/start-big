<script setup lang="ts">
/**
 * @component ImprimirEtiquetasModal
 * @description Imprimir uma etiqueta por VOLUME de cada móvel (Spec 14 §6; I7):
 * o caminhão sai com tudo identificado e o montador sabe, na obra, de que
 * ambiente é cada caixa.
 *
 * Escolhe o modelo (os prontos da marcenaria), os móveis, os volumes de cada
 * um (começa na quantidade) e a posição inicial da folha já usada. Quem
 * imprime é o motor de etiquetas (`useImpressaoEtiquetas`): no driver, ou
 * direto na térmica quando o terminal está configurado assim (D7). A
 * calibração é a do terminal (D6). Nenhum preço (D10).
 */
import { computed, ref, watch } from 'vue';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import EtiquetasImpressao from '@/shared/etiquetas/components/EtiquetasImpressao.vue';
import { PRESETS_MOVEL } from '@/shared/etiquetas/presets';
import { useImpressaoEtiquetas } from '@/shared/etiquetas/useImpressaoEtiquetas';
import { useImpressaoStore } from '@/shared/stores/impressao.store';
import { useCompanyPrintInfo } from '@/shared/utils/print.utils';

import {
  lembrarModelo, modeloLembrado, montarEtiquetas, resumoDaImpressao, volumesValidos,
  type DadosComunsEtiqueta, type MovelParaEtiqueta,
} from '../utils/montarEtiquetas';

/** Um móvel da lista do modal (a `MovelProducao` da 12B satisfaz). */
type MovelDoModal = MovelParaEtiqueta & { movel_id: number; quantidade: number; pronto: boolean };

const props = defineProps<{
  isOpen: boolean;
  numeroOs: string;
  moveis: MovelDoModal[];
  /** Os que já vêm marcados (D8: os prontos; ou só o móvel do menu). */
  marcados: number[];
  /** Projeto, endereço da obra e cliente (da OS aberta no modal). */
  obra: Omit<DadosComunsEtiqueta, 'os' | 'empresa'>;
}>();
const emit = defineEmits<{ close: [] }>();

const { trabalho, imprimir } = useImpressaoEtiquetas();
const impressao = useImpressaoStore();
const { companyInfo } = useCompanyPrintInfo();

// --- Modelo (D4, D11): o lembrado neste computador, senão o A4 em 4 -----------------
const chaveModelo = ref(PRESETS_MOVEL[0].chave);
const modelo = computed(() => PRESETS_MOVEL.find((m) => m.chave === chaveModelo.value) ?? PRESETS_MOVEL[0]);
const ehFolha = computed(() => modelo.value.definicao.pagina.tipo === 'folha');

// --- Seleção e volumes por móvel (D1) --------------------------------------------------
const selecionados = ref(new Set<number>());
const volumes = ref<Record<number, number>>({});
const comecarEm = ref(1);

// Abriu: os marcados de quem chamou; volumes = a quantidade de cada móvel.
watch(() => props.isOpen, (aberto) => {
  if (!aberto) return;
  const lembrado = modeloLembrado();
  chaveModelo.value = PRESETS_MOVEL.some((m) => m.chave === lembrado) ? lembrado! : PRESETS_MOVEL[0].chave;
  selecionados.value = new Set(props.marcados);
  volumes.value = Object.fromEntries(props.moveis.map((m) => [m.movel_id, volumesValidos(m.quantidade)]));
  comecarEm.value = 1;
}, { immediate: true });

function alternar(movelId: number) {
  const novo = new Set(selecionados.value);
  if (novo.has(movelId)) novo.delete(movelId);
  else novo.add(movelId);
  selecionados.value = novo;
}

function mudarVolumes(movelId: number, valor: string) {
  volumes.value = { ...volumes.value, [movelId]: volumesValidos(Number(valor)) };
}

/** As etiquetas, na ordem da lista (ambiente → móvel → volume). */
const etiquetas = computed(() => montarEtiquetas(
  props.moveis
    .filter((m) => selecionados.value.has(m.movel_id))
    .map((m) => ({ movel: m, volumes: volumes.value[m.movel_id] ?? 1 })),
  { ...props.obra, os: props.numeroOs, empresa: companyInfo.value.nome ?? '' },
));

/** D5: posições já usadas da folha (só vale em folha). */
const pular = computed(() => (ehFolha.value ? Math.max(0, Math.round(comecarEm.value) - 1) : 0));
const resumo = computed(() => resumoDaImpressao(modelo.value.definicao.pagina, etiquetas.value.length, pular.value));

async function confirmar() {
  if (!etiquetas.value.length) return;
  lembrarModelo(chaveModelo.value);
  // O título vira o nome sugerido do PDF (como a proposta da 07) e volta depois.
  const tituloOriginal = document.title;
  document.title = `Etiquetas ${props.numeroOs}`;
  const restaurar = () => {
    document.title = tituloOriginal;
    window.removeEventListener('afterprint', restaurar);
  };
  window.addEventListener('afterprint', restaurar);
  await imprimir({
    definicao: modelo.value.definicao,
    etiquetas: etiquetas.value,
    pular: pular.value,
    deslocamentoX: impressao.config.etiqueta_deslocamento_x_mm ?? 0,   // calibração do terminal (D6)
    deslocamentoY: impressao.config.etiqueta_deslocamento_y_mm ?? 0,
  });
  if (!trabalho.value) restaurar();                  // térmica direta: não houve diálogo
}
</script>

<template>
  <BaseModal :is-open="isOpen" :title="`Imprimir etiquetas — ${numeroOs}`" size="lg" overlay @close="emit('close')">
    <div class="flex flex-col gap-4">
      <label class="flex flex-col gap-1 text-sm font-medium text-zinc-700">
        Modelo
        <select
          v-model="chaveModelo"
          class="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-800 focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
          data-testid="modelo-etiqueta"
        >
          <option v-for="m in PRESETS_MOVEL" :key="m.chave" :value="m.chave">{{ m.nome }}<template v-if="m.descricao"> ({{ m.descricao }})</template></option>
        </select>
      </label>

      <div>
        <div class="mb-1 flex justify-between text-xs font-medium text-zinc-500">
          <span>Móveis</span><span>Volumes</span>
        </div>
        <ul class="flex flex-col gap-1">
          <li v-for="m in moveis" :key="m.movel_id" class="flex items-center gap-3 rounded-lg border border-zinc-200 px-3 py-1.5 text-sm">
            <input
              type="checkbox"
              class="h-4 w-4 accent-brand-primary"
              :checked="selecionados.has(m.movel_id)"
              :data-testid="`etiqueta-movel-${m.movel_id}`"
              @change="alternar(m.movel_id)"
            />
            <span class="min-w-0 flex-1">
              {{ m.nome }} <span class="text-zinc-500">({{ m.ambiente }})</span>
              <span v-if="!m.pronto" class="ml-1 text-xs text-zinc-400">— em produção</span>
            </span>
            <input
              type="number"
              min="1"
              max="50"
              class="w-16 rounded-lg border border-zinc-300 px-2 py-1 text-right tabular-nums"
              :value="volumes[m.movel_id]"
              :aria-label="`Volumes de ${m.nome}`"
              :data-testid="`volumes-${m.movel_id}`"
              @change="mudarVolumes(m.movel_id, ($event.target as HTMLInputElement).value)"
            />
          </li>
        </ul>
      </div>

      <label v-if="ehFolha" class="flex items-center gap-2 text-sm text-zinc-700">
        Começar na posição
        <input
          v-model.number="comecarEm"
          type="number"
          min="1"
          class="w-16 rounded-lg border border-zinc-300 px-2 py-1 text-right tabular-nums"
          data-testid="comecar-em"
        />
        <span class="text-xs text-zinc-500">(folha já usada)</span>
      </label>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-3">
        <span class="text-sm text-zinc-600" data-testid="resumo-etiquetas">{{ resumo }}</span>
        <div class="flex gap-2">
          <BaseButton variant="secondary" @click="emit('close')">Cancelar</BaseButton>
          <BaseButton :disabled="!etiquetas.length" data-testid="imprimir-etiquetas" @click="confirmar">Imprimir</BaseButton>
        </div>
      </div>
    </template>
  </BaseModal>

  <!-- As folhas que vão para o driver (o motor monta e desmonta). -->
  <EtiquetasImpressao v-if="trabalho" v-bind="trabalho" />
</template>
