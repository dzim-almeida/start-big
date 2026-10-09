<script setup lang="ts">
/**
 * @component BlocoAmbientes
 * @description Lista de ambientes e o "+ Ambiente" (Spec 06B D19, D20).
 *
 * O nome do ambiente tem SUGESTÕES (Cozinha, Closet...) e aceita texto livre.
 * Na tela "novo", adicionar o primeiro ambiente cria o orçamento (D5).
 */
import { computed, nextTick, ref } from 'vue';
import { Plus } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';

import { LIMITES, SUGESTOES_AMBIENTE } from '../../constants/orcamento.constants';
import { useEditor } from '../../composables/useEditorContexto';
import AmbienteCard from './AmbienteCard.vue';

const { detalhe, editavel, acoesOrcamento, garantirOrcamento } = useEditor();

const ambientes = computed(() => detalhe.value?.ambientes ?? []);

// --- Novo ambiente --------------------------------------------------------------
const adicionando = ref(false);
const nome = ref('');
const campo = ref<HTMLInputElement | null>(null);
const gravando = ref(false);

async function abrirCampo() {
  adicionando.value = true;
  nome.value = '';
  await nextTick();
  campo.value?.focus();                               // foco no nome do ambiente (§7.12)
}

async function confirmar() {
  const texto = nome.value.trim();
  if (!texto || gravando.value) return;
  gravando.value = true;
  try {
    // Tela "novo": o primeiro ambiente cria o orçamento (D5).
    const id = await garantirOrcamento();
    if (id == null) return;
    const novo = await acoesOrcamento.criarAmbiente(texto);
    if (novo) adicionando.value = false;
  } finally {
    gravando.value = false;
  }
}

/** Troca o ambiente de lugar com o vizinho e manda a nova ordem (D20). */
async function mover(indice: number, direcao: -1 | 1) {
  const ids = ambientes.value.map((a) => a.id);
  const alvo = indice + direcao;
  if (alvo < 0 || alvo >= ids.length) return;
  [ids[indice], ids[alvo]] = [ids[alvo], ids[indice]];
  await acoesOrcamento.ordenarAmbientes(ids);
}
</script>

<template>
  <section class="rounded-2xl border border-zinc-200 bg-white p-5" aria-labelledby="titulo-ambientes" id="bloco-ambientes">
    <div class="mb-4 flex items-center justify-between">
      <h2 id="titulo-ambientes" class="text-sm font-bold text-zinc-800">Ambientes</h2>
      <BaseButton v-if="editavel && !adicionando" variant="secondary" size="sm" data-testid="novo-ambiente" @click="abrirCampo">
        <Plus :size="14" class="mr-1" /> Ambiente
      </BaseButton>
    </div>

    <!-- Nome com sugestões (datalist): escolher ou digitar livre (D19). -->
    <div v-if="adicionando" class="mb-4 flex flex-wrap items-center gap-2">
      <input
        ref="campo"
        v-model="nome"
        list="sugestoes-ambiente"
        :maxlength="LIMITES.nomeAmbiente"
        placeholder="Nome do ambiente (ex.: Cozinha)"
        aria-label="Nome do ambiente"
        class="min-w-60 flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary/30"
        data-testid="nome-ambiente"
        @keydown.enter.prevent="confirmar"
        @keydown.esc="adicionando = false"
      />
      <datalist id="sugestoes-ambiente">
        <option v-for="sugestao in SUGESTOES_AMBIENTE" :key="sugestao" :value="sugestao" />
      </datalist>
      <BaseButton variant="primary" size="sm" :is-loading="gravando" :disabled="!nome.trim()" @click="confirmar">Adicionar</BaseButton>
      <BaseButton variant="ghost" size="sm" @click="adicionando = false">Cancelar</BaseButton>
    </div>

    <div v-if="ambientes.length" class="flex flex-col gap-3">
      <AmbienteCard
        v-for="(ambiente, indice) in ambientes"
        :key="ambiente.id"
        :ambiente="ambiente"
        :primeiro="indice === 0"
        :ultimo="indice === ambientes.length - 1"
        @subir="mover(indice, -1)"
        @descer="mover(indice, 1)"
      />
    </div>
    <p v-else-if="!adicionando" class="text-sm text-zinc-400">
      Nenhum ambiente ainda. Comece por "+ Ambiente" (ex.: Cozinha, Dormitório casal).
    </p>
  </section>
</template>
