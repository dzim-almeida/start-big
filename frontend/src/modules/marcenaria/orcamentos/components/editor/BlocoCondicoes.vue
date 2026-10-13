<script setup lang="ts">
/**
 * @component BlocoCondicoes
 * @description Desconto, sinal, validade, prazo de entrega e observações da
 * proposta (Spec 06B D18, §7.12). Tudo salva sozinho (D8).
 *
 * Validade e prazo continuam em DIAS (é o que o backend guarda), mas cada um
 * tem um calendário ao lado (remodelação item 7): escolher a data calcula os
 * dias, e mudar os dias mostra a data. A conta parte do envio (validade) e da
 * aprovação (prazo); antes deles, parte de hoje.
 *
 * Desconto em R$ maior que o total: o backend responde 422 com
 * `campo = "desconto"` e a mensagem aparece EMBAIXO do campo, sem perder o
 * valor digitado (06A Revisão 1).
 */
import { computed, ref, watch } from 'vue';

import BaseDateInput from '@/shared/components/ui/BaseDateInput/BaseDateInput.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';

import { formatDataPura } from '@/shared/utils/date.utils';

import { LIMITES } from '../../constants/orcamento.constants';
import { useEditor } from '../../composables/useEditorContexto';
import { dataBase, dataDepoisDe, diasAte } from '../../utils/diasPorData';
import CampoPercentualOuValor from './CampoPercentualOuValor.vue';

const { form, detalhe, editavel, errosPorCampo } = useEditor();

const calculo = computed(() => detalhe.value?.calculo);

/** A validade conta do envio: no rascunho ainda não há data (06A). */
const dicaValidade = computed(() => {
  const data = detalhe.value?.datas.validade;
  return data ? `até ${formatDataPura(data.slice(0, 10))}` : 'contados a partir do envio (se enviado hoje)';
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

// --- Calendário (remodelação item 7) ------------------------------------------
// Data-base de cada conta: validade conta do ENVIO; prazo, da APROVAÇÃO (06A).
// Enquanto o evento não aconteceu, a base é hoje.
const baseValidade = computed(() => dataBase(detalhe.value?.datas.envio));
const basePrazo = computed(() => dataBase(detalhe.value?.datas.aprovacao));

/**
 * Liga um campo de dias a um calendário. `get`: base + dias = a data mostrada.
 * `set`: a data escolhida vira dias, escritos no MESMO texto do campo de dias,
 * então a validação de 1 a 365 e o salvamento automático são os de sempre.
 */
function dataDoCampo(texto: typeof textoValidade, base: typeof baseValidade, erro: typeof erroValidade) {
  return computed({
    get: () => {
      const dias = Number(texto.value);
      // Dias inválidos (campo vazio, "abc"): o calendário fica vazio em vez de mostrar uma data errada.
      return Number.isInteger(dias) && dias > 0 ? dataDepoisDe(base.value, dias) : '';
    },
    set: (dataIso: string | undefined) => {
      if (!dataIso) return;                               // apagou a data: os dias ficam como estão
      const dias = diasAte(base.value, dataIso);
      if (dias < 1) {
        erro.value = 'Escolha uma data depois de hoje.';  // a data já passou (ou é a própria base)
        return;
      }
      texto.value = String(dias);                         // o watch de cima valida e salva
    },
  });
}
const dataValidade = dataDoCampo(textoValidade, baseValidade, erroValidade);
const dataPrazo = dataDoCampo(textoPrazo, basePrazo, erroPrazo);

/** Dicas embaixo: de onde a conta parte, enquanto o evento não aconteceu. */
const dicaPrazo = computed(() => (detalhe.value?.datas.aprovacao ? 'após a aprovação' : 'após a aprovação (se aprovado hoje)'));

/** Observações: textarea devolve '' quando vazio; o backend guarda null. */
const observacoes = computed({
  get: () => form.observacoes_proposta ?? '',
  set: (texto: string | null) => { form.observacoes_proposta = texto && texto.trim() ? texto : null; },
});

const CLASSE_DIAS =
  'min-h-10 w-20 rounded-md border bg-white px-3 py-2 text-sm tabular-nums text-gray-700 outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary disabled:bg-gray-100 disabled:cursor-not-allowed';
</script>

<template>
  <section id="secao-condicoes" class="scroll-mt-40 rounded-2xl border border-zinc-200 bg-white" aria-labelledby="titulo-condicoes">
    <header class="px-6 pb-4 pt-5">
      <h2 id="titulo-condicoes" class="text-base font-semibold text-zinc-900">Condições comerciais</h2>
      <p class="text-xs text-zinc-500">Saem na proposta que o cliente recebe.</p>
    </header>

    <!-- 2 colunas (Desconto | Sinal, depois Validade | Prazo): com o calendário ao lado dos
         dias (item 7), 4 colunas não cabem e o "Prazo" passava da borda da seção. -->
    <div class="grid grid-cols-1 gap-x-5 gap-y-4 px-6 pb-6 sm:grid-cols-2">
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
          <!-- ou escolhe a data no calendário (item 7): os dias se ajustam sozinhos -->
          <div class="w-36 shrink-0" data-testid="data-validade">
            <BaseDateInput v-model="dataValidade" :disabled="!editavel" />
          </div>
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
          <div class="w-36 shrink-0" data-testid="data-prazo">
            <BaseDateInput v-model="dataPrazo" :disabled="!editavel" />
          </div>
        </div>
        <p v-if="erroPrazo" class="mt-1.5 text-xs text-red-600">{{ erroPrazo }}</p>
        <p v-else class="mt-1.5 text-xs text-zinc-500">{{ dicaPrazo }}</p>
      </div>

      <div class="sm:col-span-2">
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
