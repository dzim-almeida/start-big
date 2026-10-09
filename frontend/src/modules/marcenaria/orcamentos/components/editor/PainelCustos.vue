<script setup lang="ts">
/**
 * @component PainelCustos
 * @description Custos, margens e parâmetros DESTE orçamento (Spec 06B D15,
 * §6.2). Só existe para quem vê custos (`inclui_custos`): para os outros, a
 * API nem manda estes números (06A D23).
 *
 * Recolhível e aberto por padrão; a preferência fica no navegador (é
 * conveniência de quem usa, não dado do orçamento). Sem armazenamento
 * (janela privada, bloqueio), fica aberto.
 *
 * Os parâmetros (markup, perda, custo/hora) valem só para este orçamento e
 * salvam sozinhos, como o resto do cabeçalho (D8).
 */
import { computed, ref, watch } from 'vue';
import { ChevronDown } from 'lucide-vue-next';

import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { formatCurrency } from '@/shared/utils/finance';

import { useEditor } from '../../composables/useEditorContexto';
import { bpParaPercentual, centavosParaReais, formatarBp, numeroParaTexto, percentualParaBp, reaisParaCentavos } from '../../utils/conversoes';

const emit = defineEmits<{ conferirPrecos: [] }>();

const { detalhe, form, editavel, errosPorCampo } = useEditor();

// --- Aberto/fechado, lembrado no navegador ------------------------------------
const CHAVE_PREFERENCIA = 'startbig.marcenaria.painel-custos-aberto';
function lerPreferencia(): boolean {
  try {
    return localStorage.getItem(CHAVE_PREFERENCIA) !== 'nao';   // padrão: aberto
  } catch {
    return true;                                                // sem armazenamento: aberto
  }
}
const aberto = ref(lerPreferencia());
watch(aberto, (valor) => {
  try {
    localStorage.setItem(CHAVE_PREFERENCIA, valor ? 'sim' : 'nao');
  } catch {
    // Sem armazenamento: só não lembra da próxima vez.
  }
});

// --- Números (só leitura, da API) ---------------------------------------------
/** O detalhe com custos (o TypeScript sabe quais campos existem depois do `if`). */
const comCustos = computed(() => (detalhe.value?.inclui_custos ? detalhe.value : null));
const calculo = computed(() => comCustos.value?.calculo ?? null);

/**
 * Rótulo da linha do RT (Spec 09B D9): de quem é e quanto por cento.
 * "RT — Studio Renascer (8%)" ou "RT — sem arquiteto". O % com até 2 casas,
 * as mesmas que o campo do bloco Arquiteto aceita (8,25% não vira "8,3%").
 */
const rotuloRt = computed(() => {
  const arquiteto = comCustos.value?.arquitetos[0];
  if (!arquiteto) return 'RT — sem arquiteto';
  return `RT — ${arquiteto.nome} (${numeroParaTexto(bpParaPercentual(arquiteto.rt_bp), 2)}%)`;
});

// --- Parâmetros (editáveis, salvam sozinhos) -------------------------------------
/** Texto de cada percentual enquanto o usuário digita. */
const textoMarkup = ref('');
const textoPerda = ref('');
const paraTexto = (bp: number | undefined) =>
  bp == null ? '' : bpParaPercentual(bp).toLocaleString('pt-BR', { maximumFractionDigits: 2, useGrouping: false });
watch(() => form.markup_bp, (bp) => { if (percentualDoTexto(textoMarkup.value) !== bp) textoMarkup.value = paraTexto(bp); }, { immediate: true });
watch(() => form.perda_bp, (bp) => { if (percentualDoTexto(textoPerda.value) !== bp) textoPerda.value = paraTexto(bp); }, { immediate: true });

/** "90" ou "12,5" → bp; inválido → null (o formulário não muda). */
function percentualDoTexto(texto: string): number | null {
  const numero = Number(texto.replace(',', '.'));
  return texto.trim() && Number.isFinite(numero) && numero >= 0 ? percentualParaBp(numero) : null;
}
function digitarMarkup(evento: Event) {
  textoMarkup.value = (evento.target as HTMLInputElement).value;
  const bp = percentualDoTexto(textoMarkup.value);
  if (bp != null) form.markup_bp = bp;
}
function digitarPerda(evento: Event) {
  textoPerda.value = (evento.target as HTMLInputElement).value;
  const bp = percentualDoTexto(textoPerda.value);
  if (bp != null) form.perda_bp = bp;
}

const custoHoraReais = computed({
  get: () => centavosParaReais(form.custo_hora_centavos ?? 0),
  set: (reais: number | null | undefined) => { form.custo_hora_centavos = reaisParaCentavos(reais ?? 0); },
});

const CLASSE_PERCENTUAL =
  'w-20 rounded-lg border border-zinc-200 px-2 py-1.5 text-sm tabular-nums focus:outline-none focus:ring-2 focus:ring-brand-primary/30 disabled:bg-zinc-50 disabled:text-zinc-500';
</script>

<template>
  <section v-if="comCustos && calculo" class="rounded-2xl border border-zinc-200 bg-white" aria-labelledby="titulo-custos" data-testid="painel-custos">
    <button
      type="button"
      class="flex w-full items-center justify-between px-5 py-4 cursor-pointer"
      :aria-expanded="aberto"
      @click="aberto = !aberto"
    >
      <h2 id="titulo-custos" class="text-sm font-bold text-zinc-800">Custos</h2>
      <ChevronDown :size="16" class="text-zinc-400 transition-transform" :class="aberto ? '' : '-rotate-90'" />
    </button>

    <div v-if="aberto" class="border-t border-zinc-100 px-5 pb-5 pt-3">
      <dl class="flex flex-col gap-1.5 text-sm">
        <!-- Custo por ambiente (o total de cada um vem da API) -->
        <div v-for="ambiente in comCustos.ambientes" :key="ambiente.id" class="flex justify-between text-zinc-500">
          <dt class="truncate">{{ ambiente.nome }}</dt>
          <dd class="tabular-nums">{{ formatCurrency(ambiente.custo_centavos) }}</dd>
        </div>
        <div v-if="calculo.instalacao" class="flex justify-between text-zinc-500">
          <dt>Instalação</dt>
          <dd class="tabular-nums">{{ formatCurrency(calculo.instalacao.custo_centavos) }}</dd>
        </div>
        <div class="flex justify-between border-t border-zinc-100 pt-1.5">
          <dt class="text-zinc-600">Custo total</dt>
          <dd class="tabular-nums font-medium text-zinc-800">{{ formatCurrency(calculo.custo_total_centavos) }}</dd>
        </div>
        <div class="flex justify-between">
          <dt class="text-zinc-600">Margem bruta</dt>
          <dd class="tabular-nums text-zinc-800">{{ formatCurrency(calculo.margem_bruta_centavos) }}</dd>
        </div>
        <!-- RT: sempre visível, com o nome e o % (09B D9); sem arquiteto, R$ 0,00 -->
        <div class="flex justify-between gap-3" data-testid="linha-rt">
          <dt class="truncate text-zinc-600">{{ rotuloRt }}</dt>
          <dd class="shrink-0 tabular-nums text-zinc-800">− {{ formatCurrency(calculo.rt_total_centavos) }}</dd>
        </div>
        <div class="flex justify-between border-t border-zinc-100 pt-1.5 font-semibold">
          <dt class="text-zinc-700">Margem líquida</dt>
          <dd class="text-right tabular-nums" :class="calculo.margem_liquida_centavos < 0 ? 'text-red-600' : 'text-emerald-700'">
            {{ formatCurrency(calculo.margem_liquida_centavos) }}
            <span class="block text-xs font-normal">({{ formatarBp(calculo.margem_liquida_bp) }})</span>
          </dd>
        </div>
      </dl>

      <!-- Parâmetros deste orçamento -->
      <div class="mt-5 border-t border-zinc-100 pt-4">
        <p class="text-xs font-semibold text-zinc-700">Parâmetros deste orçamento</p>
        <p class="mt-0.5 text-[11px] text-zinc-400">Valem só para este orçamento. O padrão fica em Configurações › Marcenaria.</p>

        <div class="mt-3 flex flex-col gap-3">
          <label class="flex items-center justify-between gap-3 text-xs text-zinc-600">
            Markup
            <span class="flex items-center gap-1">
              <input :value="textoMarkup" type="text" inputmode="decimal" :disabled="!editavel" :class="CLASSE_PERCENTUAL" aria-label="Markup em percentual" @input="digitarMarkup" />
              <span class="text-zinc-400">%</span>
            </span>
          </label>
          <p v-if="errosPorCampo.markup" class="text-[11px] text-red-600">{{ errosPorCampo.markup }}</p>

          <label class="flex items-center justify-between gap-3 text-xs text-zinc-600">
            Perda
            <span class="flex items-center gap-1">
              <input :value="textoPerda" type="text" inputmode="decimal" :disabled="!editavel" :class="CLASSE_PERCENTUAL" aria-label="Perda em percentual" @input="digitarPerda" />
              <span class="text-zinc-400">%</span>
            </span>
          </label>
          <p v-if="errosPorCampo.perda" class="text-[11px] text-red-600">{{ errosPorCampo.perda }}</p>

          <div class="flex items-center justify-between gap-3 text-xs text-zinc-600">
            Custo/hora
            <div class="w-32"><MoneyInput v-model="custoHoraReais" :disabled="!editavel" /></div>
          </div>
          <p v-if="errosPorCampo.custo_hora" class="text-[11px] text-red-600">{{ errosPorCampo.custo_hora }}</p>
        </div>

        <!-- Conferir preços dos insumos (O3): só no rascunho. -->
        <button
          v-if="editavel"
          type="button"
          class="mt-4 text-xs font-medium text-brand-primary hover:underline cursor-pointer"
          data-testid="conferir-precos"
          @click="emit('conferirPrecos')"
        >
          Conferir preços dos insumos
        </button>
      </div>
    </div>
  </section>
</template>
