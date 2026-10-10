<script setup lang="ts">
/**
 * @component PainelCustos
 * @description "Rentabilidade" deste orçamento (Spec 06B D15, §6.2;
 * redesign 10/2026): margem líquida em destaque, o custo detalhado, a margem
 * bruta e o RT. Só existe para quem vê custos (`inclui_custos`): para os
 * outros, a API nem manda estes números (06A D23).
 *
 * Os PARÂMETROS ficam num acordeão, fechado por padrão; a preferência fica no
 * navegador (é conveniência de quem usa, não dado do orçamento). Sem
 * armazenamento (janela privada, bloqueio), fica fechado.
 *
 * Os parâmetros (markup, perda, custo/hora) valem só para este orçamento e
 * salvam sozinhos, como o resto do cabeçalho (D8).
 */
import { computed, ref, watch } from 'vue';
import { ChevronDown, Lock } from 'lucide-vue-next';

import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { formatCurrency } from '@/shared/utils/finance';

import { useEditor } from '../../composables/useEditorContexto';
import { bpParaPercentual, centavosParaReais, formatarBp, numeroParaTexto, percentualParaBp, reaisParaCentavos } from '../../utils/conversoes';

const emit = defineEmits<{ conferirPrecos: [] }>();

const { detalhe, form, editavel, errosPorCampo } = useEditor();

// --- Aberto/fechado, lembrado no navegador ------------------------------------
const CHAVE_PREFERENCIA = 'startbig.marcenaria.parametros-preco-abertos';
function lerPreferencia(): boolean {
  try {
    return localStorage.getItem(CHAVE_PREFERENCIA) === 'sim';   // padrão: fechado
  } catch {
    return false;                                               // sem armazenamento: fechado
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

/** Largura da barra da margem líquida (0 a 100%; negativa não pinta). */
const larguraMargem = computed(() => Math.max(0, Math.min(100, (calculo.value?.margem_liquida_bp ?? 0) / 100)));

/** "Markup 90% · Perda 10% · R$ 45,00/h": o acordeão fechado ainda diz o que vale. */
const resumoParametros = computed(() => {
  const partes = [];
  if (form.markup_bp != null) partes.push(`Markup ${formatarBp(form.markup_bp)}`);
  if (form.perda_bp != null) partes.push(`Perda ${formatarBp(form.perda_bp)}`);
  partes.push(`${formatCurrency(form.custo_hora_centavos ?? 0)}/h`);
  return partes.join(' · ');
});

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
  'min-h-9 w-20 rounded-md border border-gray-300 bg-white px-2.5 py-1.5 text-right text-sm tabular-nums text-gray-700 outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary disabled:bg-gray-100 disabled:cursor-not-allowed';
</script>

<template>
  <section v-if="comCustos && calculo" class="rounded-2xl border border-zinc-200 bg-white px-6 py-5" aria-labelledby="titulo-custos" data-testid="painel-custos">
    <header class="flex items-center justify-between gap-3">
      <h2 id="titulo-custos" class="text-sm font-semibold text-zinc-900">Rentabilidade</h2>
      <span class="inline-flex items-center gap-1 text-xs text-zinc-500"><Lock :size="12" /> Só para quem vê custos</span>
    </header>

    <!-- Margem líquida em destaque -->
    <div class="mt-3 flex flex-wrap items-baseline gap-x-2.5">
      <span class="text-2xl font-bold tabular-nums" :class="calculo.margem_liquida_centavos < 0 ? 'text-red-600' : 'text-emerald-700'">
        {{ formatarBp(calculo.margem_liquida_bp) }}
      </span>
      <span class="text-sm" :class="calculo.margem_liquida_centavos < 0 ? 'text-red-600' : 'text-emerald-700'">
        margem líquida · <span class="tabular-nums">{{ formatCurrency(calculo.margem_liquida_centavos) }}</span>
      </span>
    </div>
    <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-emerald-50" aria-hidden="true">
      <div class="h-full rounded-full bg-emerald-600" :style="{ width: `${larguraMargem}%` }" />
    </div>

    <dl class="mt-4 flex flex-col gap-1.5 text-sm">
      <div class="flex justify-between gap-3">
        <dt class="text-zinc-600">Custo total</dt>
        <dd class="tabular-nums font-medium text-zinc-800">{{ formatCurrency(calculo.custo_total_centavos) }}</dd>
      </div>
      <!-- Custo por ambiente e da instalação (o total de cada um vem da API) -->
      <div v-for="ambiente in comCustos.ambientes" :key="ambiente.id" class="flex justify-between gap-3 pl-3 text-xs text-zinc-500">
        <dt class="truncate">{{ ambiente.nome }}</dt>
        <dd class="tabular-nums">{{ formatCurrency(ambiente.custo_centavos) }}</dd>
      </div>
      <div v-if="calculo.instalacao" class="flex justify-between gap-3 pl-3 text-xs text-zinc-500">
        <dt>Instalação</dt>
        <dd class="tabular-nums">{{ formatCurrency(calculo.instalacao.custo_centavos) }}</dd>
      </div>
      <div class="flex justify-between gap-3 border-t border-zinc-100 pt-1.5">
        <dt class="text-zinc-600">Margem bruta</dt>
        <dd class="tabular-nums text-zinc-800">{{ formatCurrency(calculo.margem_bruta_centavos) }}</dd>
      </div>
      <!-- RT: sempre visível, com o nome e o % (09B D9); sem arquiteto, R$ 0,00 -->
      <div class="flex justify-between gap-3" data-testid="linha-rt">
        <dt class="truncate text-zinc-600">{{ rotuloRt }}</dt>
        <dd class="shrink-0 tabular-nums text-zinc-800">− {{ formatCurrency(calculo.rt_total_centavos) }}</dd>
      </div>
    </dl>

    <!-- Parâmetros deste orçamento (salvam sozinhos, D8) -->
    <div class="mt-4 overflow-hidden rounded-xl border border-zinc-200">
      <button
        type="button"
        class="flex w-full items-center justify-between gap-3 bg-zinc-50 px-3.5 py-2.5 text-left cursor-pointer"
        :aria-expanded="aberto"
        data-testid="abrir-parametros"
        @click="aberto = !aberto"
      >
        <span class="min-w-0">
          <span class="block text-sm font-semibold text-zinc-900">Parâmetros de preço</span>
          <span class="block truncate text-xs tabular-nums text-zinc-500">{{ resumoParametros }}</span>
        </span>
        <ChevronDown :size="16" class="shrink-0 text-zinc-400 transition-transform" :class="aberto ? 'rotate-180' : ''" />
      </button>

      <div v-if="aberto" class="flex flex-col gap-3 border-t border-zinc-200 px-3.5 py-3.5">
        <p class="text-xs text-zinc-500">Valem só para este orçamento. O padrão fica em Configurações › Marcenaria.</p>

        <label class="flex items-center justify-between gap-3 text-sm text-zinc-600">
          Markup
          <span class="flex items-center gap-1.5">
            <input :value="textoMarkup" type="text" inputmode="decimal" :disabled="!editavel" :class="CLASSE_PERCENTUAL" aria-label="Markup em percentual" @input="digitarMarkup" />
            <span class="text-zinc-500">%</span>
          </span>
        </label>
        <p v-if="errosPorCampo.markup" class="text-xs text-red-600">{{ errosPorCampo.markup }}</p>

        <label class="flex items-center justify-between gap-3 text-sm text-zinc-600">
          Perda
          <span class="flex items-center gap-1.5">
            <input :value="textoPerda" type="text" inputmode="decimal" :disabled="!editavel" :class="CLASSE_PERCENTUAL" aria-label="Perda em percentual" @input="digitarPerda" />
            <span class="text-zinc-500">%</span>
          </span>
        </label>
        <p v-if="errosPorCampo.perda" class="text-xs text-red-600">{{ errosPorCampo.perda }}</p>

        <div class="flex items-center justify-between gap-3 text-sm text-zinc-600">
          Custo/hora
          <div class="w-32"><MoneyInput v-model="custoHoraReais" :disabled="!editavel" /></div>
        </div>
        <p v-if="errosPorCampo.custo_hora" class="text-xs text-red-600">{{ errosPorCampo.custo_hora }}</p>
      </div>
    </div>

    <!-- Conferir preços dos insumos (O3): só no rascunho. -->
    <button
      v-if="editavel"
      type="button"
      class="mt-3 text-xs font-semibold text-brand-primary hover:underline cursor-pointer"
      data-testid="conferir-precos"
      @click="emit('conferirPrecos')"
    >
      Conferir preços dos insumos
    </button>
  </section>
</template>
