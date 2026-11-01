<script setup lang="ts">
/**
 * @component CfopDaNotaCampo
 * @description "CFOP desta nota" na conferência da NF-e: trocar o CFOP só para
 * esta nota, sem ir ao cadastro do produto.
 *
 * C2 de docs/nfe-cfop-e-notas-da-os-plano.md. Decisões do Alan (01/11/2026):
 * - um campo para a nota toda, com pesquisa; numa nota mista (peça sem ST +
 *   peça com ST) um campo por GRUPO, nunca por item (D1/D1a);
 * - o CSOSN e a natureza acompanham sozinhos — quem decide é o backend, que
 *   devolve a prévia nova (D2);
 * - a troca vale só para a nota; a caixinha grava no cadastro (D4).
 *
 * As opções vêm do backend (`grupos_cfop`), já filtradas pela família do CFOP:
 * a tela não decide o que pode virar o quê.
 */
import { computed } from 'vue';
import { ArrowRightLeft, Lock } from 'lucide-vue-next';

import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import type { GrupoCfop } from '../../types/fiscal.types';

const props = defineProps<{
  grupos: GrupoCfop[];
  disabled?: boolean;
}>();

const trocas = defineModel<Record<string, string>>('trocas', { default: () => ({}) });
const comoPadrao = defineModel<boolean>('comoPadrao', { default: false });
const emit = defineEmits<{ (e: 'alterou'): void }>();

const umGrupoSo = computed(() => props.grupos.length === 1);
const houveTroca = computed(() => Object.keys(trocas.value).length > 0);

function opcoesDo(grupo: GrupoCfop) {
  return grupo.opcoes.map((o) => ({ value: o.cfop, label: o.descricao ? `${o.cfop} – ${o.descricao}` : o.cfop }));
}

function rotuloDo(grupo: GrupoCfop): string {
  if (umGrupoSo.value) return 'CFOP desta nota';
  const itens = grupo.itens.length === 1 ? `Item ${grupo.itens[0]}` : `Itens ${grupo.itens.join(', ')}`;
  return `${itens} (sugerido ${grupo.cfop_sugerido})`;
}

function escolher(grupo: GrupoCfop, cfop: string | number | undefined) {
  const valor = String(cfop ?? '');
  if (!valor || valor === grupo.cfop) return;
  const novas = { ...trocas.value };
  if (valor === grupo.cfop_sugerido) delete novas[grupo.cfop_sugerido];
  else novas[grupo.cfop_sugerido] = valor;
  trocas.value = novas;
  if (!Object.keys(novas).length) comoPadrao.value = false;
  emit('alterou');
}
</script>

<template>
  <div v-if="grupos.length" class="rounded-xl border border-zinc-200 bg-white overflow-hidden" data-cfop-da-nota>
    <div class="flex items-center gap-2 px-4 py-2.5 bg-zinc-50 border-b border-zinc-100">
      <ArrowRightLeft :size="14" class="text-zinc-400" />
      <h4 class="text-xs font-semibold uppercase tracking-wider text-zinc-500">CFOP</h4>
    </div>
    <div class="p-4 space-y-3">
      <div v-for="grupo in grupos" :key="grupo.cfop_sugerido" :data-grupo="grupo.cfop_sugerido">
        <BaseSelect
          v-if="grupo.opcoes.length"
          :model-value="grupo.cfop"
          :options="opcoesDo(grupo)"
          :label="rotuloDo(grupo)"
          :disabled="disabled"
          placeholder="Pesquise pelo número ou pelo nome"
          @update:model-value="escolher(grupo, $event)"
        />
        <div v-else class="text-xs text-zinc-600">
          <p class="font-medium text-zinc-700">{{ rotuloDo(grupo) }}</p>
          <p class="mt-1 flex items-center gap-1.5">
            <Lock :size="12" class="text-zinc-400" />
            <span class="font-mono">{{ grupo.cfop }}</span>
            <span v-if="grupo.descricao">– {{ grupo.descricao }}</span>
            <span class="text-zinc-400">(definido pela operação)</span>
          </p>
        </div>
      </div>

      <div v-if="houveTroca" class="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 space-y-2" data-aviso-troca>
        <p class="text-xs text-amber-800 leading-relaxed">
          <strong>Diferente do cadastro do produto.</strong> A situação do ICMS e a natureza da
          operação acompanham o CFOP escolhido. A troca vale só para esta nota.
        </p>
        <BaseCheckbox v-model="comoPadrao" label="Usar como padrão dos produtos trocados" :disabled="disabled" />
      </div>
    </div>
  </div>
</template>
