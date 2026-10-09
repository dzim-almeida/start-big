<script setup lang="ts">
/**
 * @component BlocoArquiteto
 * @description Quem indicou o cliente e o RT dele (Spec 09B D1-D8, D12).
 *
 * - "Quem indicou": arquitetos ativos do cadastro de fornecedores (tipo
 *   `arquiteto`), ou "Nenhum". Escolher salva na hora (PUT /rt pela fila).
 * - Só com custos: o campo "RT (%)" (salva sozinho, 800 ms), quanto o
 *   arquiteto recebe e o efeito do modo do RT no preço.
 * - Sem custos: o vendedor escolhe o arquiteto; o % vem do padrão (P4).
 * - "Cadastrar arquiteto" abre o cadastro de fornecedor já no tipo arquiteto
 *   e, ao salvar, seleciona o novo (sem sair do orçamento).
 */
import { computed, ref, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { AlertTriangle, Plus } from 'lucide-vue-next';

import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { useFornecedorModal } from '@/modules/products/suppliers/composables/useFornecedorModal';
import { FORNECEDORES_QUERY_KEY } from '@/modules/products/shared/constants/queryKeys';
import { formatCurrency } from '@/shared/utils/finance';

import { avisoRtZero } from '../../constants/avisos.constants';
import { useEditor } from '../../composables/useEditorContexto';
import { usePermissoesOrcamento } from '../../composables/usePermissoesOrcamento';
import { getArquitetos } from '../../services/orcamento.service';
import { bpParaPercentual, lerNumeroDigitado, numeroParaTexto, percentualParaBp } from '../../utils/conversoes';

const { detalhe, form, editavel, incluiCustos, acoesOrcamento, garantirOrcamento } = useEditor();
const { podeCadastrarFornecedor } = usePermissoesOrcamento();

/** Um arquiteto por orçamento na tela (C5a): o primeiro da lista. */
const atual = computed(() => detalhe.value?.arquitetos[0] ?? null);

// --- Lista de arquitetos ------------------------------------------------------------
// Rota própria do orçamento (só id, nome e escritório; vale a permissão de ver
// orçamentos). A chave começa pela dos fornecedores: cadastrar um fornecedor
// novo invalida essa raiz e esta lista recarrega junto.
const { data: arquitetos } = useQuery({
  queryKey: [FORNECEDORES_QUERY_KEY, 'marcenaria', 'arquitetos'],
  queryFn: getArquitetos,                                   // o backend já filtra os ativos e ordena (D4)
  enabled: editavel,                                        // fora do rascunho, o nome basta
  staleTime: 60_000,
});
const opcoes = computed(() => {
  const lista = (arquitetos.value ?? [])
    .map((a) => ({ value: a.id, label: a.nome_fantasia ? `${a.nome} · ${a.nome_fantasia}` : a.nome }));
  // O gravado aparece mesmo que a lista não carregue (ou que ele tenha sido inativado).
  if (atual.value && !lista.some((o) => o.value === atual.value!.fornecedor_id)) {
    lista.unshift({ value: atual.value.fornecedor_id, label: atual.value.nome });
  }
  return [{ value: 0, label: 'Nenhum' }, ...lista];
});

const gravando = ref(false);
/** Escolher salva na hora (D7). 0 = "Nenhum" (lista vazia no PUT). */
async function escolher(valor: string | number | undefined) {
  const id = Number(valor) || null;
  if (id === (atual.value?.fornecedor_id ?? null)) return;
  gravando.value = true;
  try {
    if ((await garantirOrcamento()) == null) return;        // tela "novo": cria antes (D5 da 06B)
    await acoesOrcamento.definirArquiteto(id);
  } finally {
    gravando.value = false;
  }
}
const selecionado = computed({
  get: () => atual.value?.fornecedor_id ?? 0,
  set: (valor: string | number | undefined) => { void escolher(valor); },
});

/** "Cadastrar arquiteto": cadastro já no tipo, e o novo vira o escolhido (D4, D5). */
const { openCreateModalWithCallback } = useFornecedorModal();
function cadastrar() {
  openCreateModalWithCallback('arquiteto', (novo) => { void escolher(novo.id); });
}

// --- RT (%), só com custos -------------------------------------------------------------
const textoRt = ref('');
const erroRt = ref('');
watch(() => form.rt_arquiteto_bp, (bp) => {
  if (bp == null) { textoRt.value = ''; return; }
  if (percentualParaBp(lerNumeroDigitado(textoRt.value) ?? -1) !== bp) textoRt.value = numeroParaTexto(bpParaPercentual(bp), 2);
}, { immediate: true });

/** Só número válido (0 a 30%, como o backend) vai para o salvamento automático. */
function digitarRt(evento: Event) {
  textoRt.value = (evento.target as HTMLInputElement).value;
  const percentual = lerNumeroDigitado(textoRt.value);
  if (percentual == null || percentual > 30) {
    erroRt.value = 'O RT deve ficar entre 0% e 30%.';
    return;
  }
  erroRt.value = '';
  form.rt_arquiteto_bp = percentualParaBp(percentual);
}

/** Com custos: quanto recebe e o que o modo faz com o preço (D6). */
const comCustos = computed(() => (detalhe.value?.inclui_custos ? detalhe.value : null));
const arquitetoComCustos = computed(() => comCustos.value?.arquitetos[0] ?? null);
const fraseModo = computed(() =>
  comCustos.value?.parametros.rt_modo === 'PRECO'
    ? 'Modo: embutido no preço — os preços sobem para cobrir o RT.'
    : 'Modo: sai da margem — o preço do orçamento não muda.',
);
/** D12: arquiteto com 0% (o padrão nasce em 0%): o RT seria esquecido. */
const semPercentual = computed(() => avisoRtZero(detalhe.value));

const CLASSE_PERCENTUAL =
  'w-20 rounded-lg border px-2 py-1.5 text-sm tabular-nums focus:outline-none focus:ring-2 focus:ring-brand-primary/30 disabled:bg-zinc-50 disabled:text-zinc-500';
</script>

<template>
  <section class="rounded-2xl border border-zinc-200 bg-white p-5" aria-labelledby="titulo-arquiteto" data-testid="bloco-arquiteto">
    <h2 id="titulo-arquiteto" class="mb-3 text-sm font-bold text-zinc-800">Arquiteto</h2>

    <!-- Fora do rascunho: só leitura (D8). -->
    <p v-if="!editavel" class="text-sm text-zinc-700" data-testid="arquiteto-leitura">
      {{ atual ? atual.nome : 'Nenhum arquiteto indicou este cliente.' }}
    </p>

    <div v-else class="flex flex-wrap items-end gap-4">
      <div class="w-72">
        <BaseSelect v-model="selecionado" label="Quem indicou" :options="opcoes" :disabled="gravando" placeholder="Nenhum" />
      </div>
      <button
        v-if="podeCadastrarFornecedor"
        type="button"
        class="mb-2 inline-flex items-center gap-1 text-xs font-medium text-brand-primary hover:underline cursor-pointer"
        data-testid="cadastrar-arquiteto"
        @click="cadastrar"
      >
        <Plus :size="12" /> Cadastrar arquiteto
      </button>
    </div>

    <!-- Só com custos (D1, D6, D12) -->
    <div v-if="incluiCustos && arquitetoComCustos" class="mt-4 flex flex-col gap-1.5" data-testid="rt-com-custos">
      <label class="flex items-center gap-2 text-xs text-zinc-600">
        RT
        <input
          :value="textoRt"
          type="text"
          inputmode="decimal"
          :disabled="!editavel"
          :class="[CLASSE_PERCENTUAL, erroRt ? 'border-red-400' : 'border-zinc-200']"
          aria-label="RT do arquiteto em percentual"
          data-testid="rt-percentual"
          @input="digitarRt"
        />
        <span class="text-zinc-400">%</span>
      </label>
      <p v-if="erroRt" class="text-[11px] text-red-600">{{ erroRt }}</p>
      <p class="text-xs text-zinc-600" data-testid="rt-previsto">
        {{ arquitetoComCustos.nome }} recebe <strong class="tabular-nums">{{ formatCurrency(arquitetoComCustos.valor_previsto_centavos) }}</strong>
      </p>
      <p class="text-[11px] text-zinc-400">{{ fraseModo }}</p>
      <p v-if="semPercentual" class="mt-1 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900" data-testid="aviso-rt-zero">
        <AlertTriangle :size="14" class="mt-0.5 shrink-0" />
        {{ semPercentual.texto }}
      </p>
    </div>
  </section>
</template>
