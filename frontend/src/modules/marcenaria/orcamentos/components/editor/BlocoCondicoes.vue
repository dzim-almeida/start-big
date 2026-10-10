<script setup lang="ts">
/**
 * @component BlocoCondicoes
 * @description Desconto, sinal, validade, prazo de entrega e observações da
 * proposta (Spec 06B D18, §7.12). Tudo salva sozinho (D8).
 *
 * Desconto em R$ maior que o total: o backend responde 422 com
 * `campo = "desconto"` e a mensagem aparece EMBAIXO do campo, sem perder o
 * valor digitado (06A Revisão 1).
 */
import { computed, ref, watch } from 'vue';

import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';

import { formatDataPura } from '@/shared/utils/date.utils';

import { LIMITES } from '../../constants/orcamento.constants';
import { useEditor } from '../../composables/useEditorContexto';
import CampoPercentualOuValor from './CampoPercentualOuValor.vue';

const { form, detalhe, editavel, errosPorCampo } = useEditor();

const calculo = computed(() => detalhe.value?.calculo);

/** A validade conta do envio: no rascunho ainda não há data (06A). */
const dicaValidade = computed(() => {
  const data = detalhe.value?.datas.validade;
  return data ? `até ${formatDataPura(data.slice(0, 10))}` : 'contados a partir do envio';
});
const caracteresObservacoes = computed(() => (form.observacoes_proposta ?? '').length);

// --- Dias (validade e prazo): inteiros de 1 a 365, as regras da 04A ---------
/** Texto de cada campo de dias (o formulário só recebe número válido). */
const textoValidade = ref(String(form.validade_dias));
const textoPrazo = ref(String(form.prazo_entrega_dias));
const erroValidade = ref('');
const erroPrazo = ref('');

/** "15" → 15; fora de 1..365 ou não inteiro → mensagem. */
function lerDias(texto: string): { dias: number | null; erro: string } {
  const dias = Number(texto);
  if (!texto.trim() || !Number.isInteger(dias) || dias < LIMITES.diasMin || dias > LIMITES.diasMax) {
    return { dias: null, erro: `Use um número inteiro de ${LIMITES.diasMin} a ${LIMITES.diasMax} dias.` };
  }
  return { dias, erro: '' };
}

watch(textoValidade, (texto) => {
  const { dias, erro } = lerDias(texto);
  erroValidade.value = erro;
  if (dias != null) form.validade_dias = dias;              // só número válido vai para o salvamento
});
watch(textoPrazo, (texto) => {
  const { dias, erro } = lerDias(texto);
  erroPrazo.value = erro;
  if (dias != null) form.prazo_entrega_dias = dias;
});
// Valor novo vindo do servidor (outro computador, nova versão): atualiza o texto.
watch(() => form.validade_dias, (dias) => { if (Number(textoValidade.value) !== dias) textoValidade.value = String(dias); });
watch(() => form.prazo_entrega_dias, (dias) => { if (Number(textoPrazo.value) !== dias) textoPrazo.value = String(dias); });

/** Observações: textarea devolve '' quando vazio; o backend guarda null. */
const observacoes = computed({
  get: () => form.observacoes_proposta ?? '',
  set: (texto: string | null) => { form.observacoes_proposta = texto && texto.trim() ? texto : null; },
});

const CLASSE_DIAS =
  'min-h-10 w-24 rounded-md border bg-white px-3 py-2 text-sm tabular-nums text-gray-700 outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary disabled:bg-gray-100 disabled:cursor-not-allowed';
</script>

<template>
  <section id="secao-condicoes" class="scroll-mt-40 rounded-2xl border border-zinc-200 bg-white" aria-labelledby="titulo-condicoes">
    <header class="px-6 pb-4 pt-5">
      <h2 id="titulo-condicoes" class="text-base font-semibold text-zinc-900">Condições comerciais</h2>
      <p class="text-xs text-zinc-500">Saem na proposta que o cliente recebe.</p>
    </header>

    <div class="grid grid-cols-1 gap-x-5 gap-y-4 px-6 pb-6 sm:grid-cols-2 xl:grid-cols-4">
      <CampoPercentualOuValor
        v-model="form.desconto"
        nome="desconto"
        rotulo="Desconto"
        :equivalente-centavos="calculo?.desconto_centavos ?? null"
        :equivalente-bp="calculo?.desconto_bp_efetivo ?? null"
        :erro="errosPorCampo.desconto"
        :disabled="!editavel"
      />
      <CampoPercentualOuValor
        v-model="form.sinal"
        nome="sinal"
        rotulo="Sinal na aprovação"
        :equivalente-centavos="calculo?.sinal_centavos ?? null"
        :equivalente-bp="calculo?.sinal_bp_efetivo ?? null"
        :erro="errosPorCampo.sinal"
        :disabled="!editavel"
      />

      <div>
        <label for="validade-dias" class="mb-1.5 block text-xs font-medium text-zinc-600">Validade</label>
        <div class="flex items-center gap-2">
          <input
            id="validade-dias"
            v-model="textoValidade"
            type="text"
            inputmode="numeric"
            :disabled="!editavel"
            :class="[CLASSE_DIAS, erroValidade ? 'border-red-400' : 'border-gray-300']"
          />
          <span class="text-sm text-zinc-500">dias</span>
        </div>
        <p v-if="erroValidade" class="mt-1.5 text-xs text-red-600">{{ erroValidade }}</p>
        <p v-else class="mt-1.5 text-xs text-zinc-500">{{ dicaValidade }}</p>
      </div>
      <div>
        <label for="prazo-dias" class="mb-1.5 block text-xs font-medium text-zinc-600">Prazo de entrega</label>
        <div class="flex items-center gap-2">
          <input
            id="prazo-dias"
            v-model="textoPrazo"
            type="text"
            inputmode="numeric"
            :disabled="!editavel"
            :class="[CLASSE_DIAS, erroPrazo ? 'border-red-400' : 'border-gray-300']"
          />
          <span class="text-sm text-zinc-500">dias</span>
        </div>
        <p v-if="erroPrazo" class="mt-1.5 text-xs text-red-600">{{ erroPrazo }}</p>
        <p v-else class="mt-1.5 text-xs text-zinc-500">após a aprovação</p>
      </div>

      <div class="sm:col-span-2 xl:col-span-4">
        <BaseTextarea
          v-model="observacoes"
          label="Observações da proposta"
          placeholder="Ex.: saldo em 3x no cartão; projeto 3D aprovado em 01/10."
          :rows="3"
          :disabled="!editavel"
        />
        <p class="mt-1.5 flex justify-between gap-4 text-xs text-zinc-500">
          <span>Sai na proposta, com as quebras de linha.</span>
          <span class="tabular-nums">{{ caracteresObservacoes }} / {{ LIMITES.textoLongo }}</span>
        </p>
      </div>
    </div>
  </section>
</template>
