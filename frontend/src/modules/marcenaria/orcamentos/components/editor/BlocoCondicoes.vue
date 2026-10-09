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

import { LIMITES } from '../../constants/orcamento.constants';
import { useEditor } from '../../composables/useEditorContexto';
import CampoPercentualOuValor from './CampoPercentualOuValor.vue';

const { form, detalhe, editavel, errosPorCampo } = useEditor();

const calculo = computed(() => detalhe.value?.calculo);

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
  'w-24 rounded-lg border px-3 py-2 text-sm tabular-nums focus:outline-none focus:ring-2 focus:ring-brand-primary/30 disabled:bg-zinc-50 disabled:text-zinc-500';
</script>

<template>
  <section class="rounded-2xl border border-zinc-200 bg-white p-5" aria-labelledby="titulo-condicoes">
    <h2 id="titulo-condicoes" class="mb-4 text-sm font-bold text-zinc-800">Condições</h2>

    <div class="grid grid-cols-1 gap-5 md:grid-cols-2">
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
        <label for="validade-dias" class="mb-1 block text-xs font-medium text-zinc-600">Validade</label>
        <input
          id="validade-dias"
          v-model="textoValidade"
          type="text"
          inputmode="numeric"
          :disabled="!editavel"
          :class="[CLASSE_DIAS, erroValidade ? 'border-red-400' : 'border-zinc-200']"
        />
        <span class="ml-2 text-xs text-zinc-400">dias</span>
        <p v-if="erroValidade" class="mt-1 text-[11px] text-red-600">{{ erroValidade }}</p>
      </div>
      <div>
        <label for="prazo-dias" class="mb-1 block text-xs font-medium text-zinc-600">Prazo de entrega</label>
        <input
          id="prazo-dias"
          v-model="textoPrazo"
          type="text"
          inputmode="numeric"
          :disabled="!editavel"
          :class="[CLASSE_DIAS, erroPrazo ? 'border-red-400' : 'border-zinc-200']"
        />
        <span class="ml-2 text-xs text-zinc-400">dias após a aprovação</span>
        <p v-if="erroPrazo" class="mt-1 text-[11px] text-red-600">{{ erroPrazo }}</p>
      </div>
    </div>

    <div class="mt-5">
      <BaseTextarea
        v-model="observacoes"
        label="Observações da proposta"
        placeholder="Ex.: saldo em 3x no cartão; projeto 3D aprovado em 01/10."
        :rows="3"
        :disabled="!editavel"
      />
      <p class="mt-1 text-[11px] text-zinc-400">Sai na proposta, com as quebras de linha. Até {{ LIMITES.textoLongo }} caracteres.</p>
    </div>
  </section>
</template>
