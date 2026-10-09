<script setup lang="ts">
/**
 * @component AprovarModal
 * @description Aprovar o orçamento e gerar a OS (Spec 08B §4.1-4.2, §6.1).
 *
 * Três blocos, na ordem da conversa com o cliente:
 *   1. O que o cliente aprovou (móveis e instalação, com caixas);
 *   2. Valores (desconto renegociável e a prévia: total, sinal, saldo, entrega);
 *   3. Sinal: "O cliente já pagou o sinal?" SEM resposta marcada (D8).
 *
 * Todo número vem da API (`/aprovacao/simular`, 400 ms depois de cada mudança,
 * C8). Quem grava é o editor, pela fila (função `aprovar` recebida por prop).
 */
import { computed, ref, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { AlertTriangle } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseCheckbox from '@/shared/components/ui/BaseCheckbox/BaseCheckbox.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { getPaymentMethodsAll } from '@/shared/services/paymentMethods.service';
import { formatDataPura } from '@/shared/utils/date.utils';
import { formatCurrency } from '@/shared/utils/finance';

import { CHAVE_RAIZ } from '../../constants/orcamento.constants';
import { useSimularAprovacao } from '../../composables/useSimularAprovacao';
import { aprovarFormSchema, type AprovacaoEntrada, type AprovarForm } from '../../schemas/aprovacao.schema';
import type { OrcamentoDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import { centavosParaReais, formatarBp, formatarMedidas, reaisParaCentavos } from '../../utils/conversoes';
import { campoDoErro, mensagemDoErro } from '../../utils/erros';
import CampoPercentualOuValor from '../editor/CampoPercentualOuValor.vue';

const props = defineProps<{
  isOpen: boolean;
  detalhe: OrcamentoDetalhe;
  /** Grava pela fila; devolve true se aprovou (o editor abre o OSCriadaModal). */
  aprovar: (entrada: AprovacaoEntrada) => Promise<boolean>;
}>();

const emit = defineEmits<{ close: [] }>();

// --- Móveis que podem ser aprovados ----------------------------------------------
/** Móvel com preço zero não pode ser aprovado (08A D4): a caixa fica travada. */
const semPreco = (precoCentavos: number | undefined) => !precoCentavos;
const idsAprovaveis = computed(() =>
  props.detalhe.ambientes.flatMap((a) => a.moveis.filter((m) => !semPreco(m.calculo?.preco_total_centavos)).map((m) => m.id)),
);
const temInstalacao = computed(() => props.detalhe.calculo.instalacao != null);

// --- Formulário --------------------------------------------------------------------
function formInicial(): AprovarForm {
  return {
    movel_ids: [...idsAprovaveis.value],                     // todos marcados (D2)
    incluir_instalacao: temInstalacao.value,
    desconto: { ...props.detalhe.desconto },                 // começa com o do orçamento
    sinal_recebido: null,                                    // D8: sem resposta marcada
    sinal_valor_centavos: 0,
    forma_pagamento_id: null,
    usar_credito_cliente: false,
  };
}
const form = ref<AprovarForm>(formInicial());
const valorSinalTocado = ref(false);                         // o usuário mudou o valor recebido?
const mexeu = ref(false);                                    // para perguntar ao fechar
const tentouAprovar = ref(false);
const gravando = ref(false);

// Cada abertura começa do zero (`immediate`: também se já nascer aberto).
watch(() => props.isOpen, (aberto) => {
  if (!aberto) return;
  form.value = formInicial();
  valorSinalTocado.value = false;
  mexeu.value = false;
  tentouAprovar.value = false;
}, { immediate: true });
watch(form, () => { mexeu.value = true; }, { deep: true, flush: 'sync' });

// --- Prévia (D3) ------------------------------------------------------------------------
const descontoMudou = computed(() => JSON.stringify(form.value.desconto) !== JSON.stringify(props.detalhe.desconto));
const entradaSimulacao = computed<AprovacaoEntrada>(() => ({
  movel_ids: form.value.movel_ids,
  incluir_instalacao: form.value.incluir_instalacao,
  ...(descontoMudou.value ? { desconto: form.value.desconto } : {}),   // ausente = o do orçamento (08A D11)
}));
const { data: previa, isFetching, error: erroPrevia } = useSimularAprovacao(
  computed(() => props.detalhe.id),
  entradaSimulacao,
  computed(() => props.isOpen),
);
/** 422 do motor com `campo: "desconto"` vai para baixo do campo (D3). */
const erroDesconto = computed(() => (campoDoErro(erroPrevia.value) === 'desconto' ? mensagemDoErro(erroPrevia.value) : ''));
const erroGeralPrevia = computed(() => (erroPrevia.value && !erroDesconto.value ? mensagemDoErro(erroPrevia.value) : ''));

// O valor recebido começa com o sinal combinado (D9), até o usuário mexer nele.
watch(() => previa.value?.sinal_centavos, (sinal) => {
  if (sinal == null || valorSinalTocado.value) return;
  const antes = mexeu.value;                                  // preencher sozinho não conta como "mexeu"
  form.value.sinal_valor_centavos = sinal;
  mexeu.value = antes;
});
const sinalCombinado = computed(() => previa.value?.sinal_centavos ?? 0);
const temSinal = computed(() => sinalCombinado.value > 0);   // D11: sinal zero, nada a perguntar
const credito = computed(() => previa.value?.credito_cliente_centavos ?? 0);

// --- Formas de pagamento (só as ativas) ------------------------------------------------
const { data: formas } = useQuery({
  queryKey: [CHAVE_RAIZ, 'formas-pagamento'],
  queryFn: getPaymentMethodsAll,
  enabled: computed(() => props.isOpen && form.value.sinal_recebido === true),
  staleTime: 5 * 60 * 1000,
});
const opcoesForma = computed(() => (formas.value ?? []).filter((f) => f.ativo).map((f) => ({ value: f.id, label: f.nome })));
const forma = computed({
  get: () => form.value.forma_pagamento_id ?? undefined,
  set: (valor: string | number | undefined) => { form.value.forma_pagamento_id = valor == null || valor === '' ? null : Number(valor); },
});
const valorRecebidoReais = computed({
  get: () => centavosParaReais(form.value.sinal_valor_centavos),
  set: (reais: number | null | undefined) => {
    valorSinalTocado.value = true;
    form.value.sinal_valor_centavos = reaisParaCentavos(reais ?? 0);
  },
});

// --- Caixas -----------------------------------------------------------------------------
function marcado(id: number) {
  return form.value.movel_ids.includes(id);
}
function alternar(id: number) {
  form.value.movel_ids = marcado(id) ? form.value.movel_ids.filter((m) => m !== id) : [...form.value.movel_ids, id];
}
/** "Todos" / "Nenhum" de um ambiente (só os móveis com preço). */
function marcarAmbiente(ambienteId: number, marcar: boolean) {
  const ids = props.detalhe.ambientes.find((a) => a.id === ambienteId)?.moveis
    .filter((m) => !semPreco(m.calculo?.preco_total_centavos)).map((m) => m.id) ?? [];
  const resto = form.value.movel_ids.filter((id) => !ids.includes(id));
  form.value.movel_ids = marcar ? [...resto, ...ids] : resto;
}

// --- Validação e envio -----------------------------------------------------------------
const validacao = computed(() => {
  // Sem sinal combinado, a pergunta não existe: conta como "ainda não" (D11).
  const comResposta = temSinal.value ? form.value : { ...form.value, sinal_recebido: form.value.sinal_recebido ?? false };
  return aprovarFormSchema.safeParse(comResposta);
});
const erros = computed<Record<string, string>>(() => {
  if (validacao.value.success) return {};
  return Object.fromEntries(validacao.value.error.issues.map((i) => [String(i.path[0]), i.message]));
});
/** D6: sem móvel marcado, sem resposta do sinal, ou com a prévia carregando/errada, não aprova. */
const podeAprovar = computed(() =>
  validacao.value.success && !isFetching.value && !erroPrevia.value && !!previa.value && !gravando.value,
);

async function confirmar() {
  tentouAprovar.value = true;
  if (!podeAprovar.value) return;
  const f = form.value;
  const recebido = temSinal.value && f.sinal_recebido === true;
  gravando.value = true;
  try {
    const ok = await props.aprovar({
      ...entradaSimulacao.value,
      sinal: recebido
        ? {
          recebido: true,
          valor_centavos: f.sinal_valor_centavos,
          forma_pagamento_id: f.usar_credito_cliente ? null : f.forma_pagamento_id,
          usar_credito_cliente: f.usar_credito_cliente,
        }
        : { recebido: false },
    });
    if (ok) emit('close');
  } finally {
    gravando.value = false;
  }
}

// --- Fechar ------------------------------------------------------------------------------
const perguntandoDescarte = ref(false);
function pedirFechar() {
  if (mexeu.value) perguntandoDescarte.value = true;
  else emit('close');
}

/** Aviso do topo conforme o status (D5). */
const avisoStatus = computed(() => {
  if (props.detalhe.status === 'RASCUNHO') return 'O orçamento será registrado como enviado e aprovado ao mesmo tempo.';
  if (props.detalhe.status === 'VENCIDO') {
    return `A validade terminou em ${formatDataPura(props.detalhe.datas.validade)}. Os preços podem ter mudado desde o envio.`;
  }
  return '';
});
</script>

<template>
  <BaseModal :is-open="isOpen" :title="`Aprovar orçamento ${detalhe.codigo} v${detalhe.versao}`" size="xl" @close="pedirFechar">
    <p v-if="avisoStatus" class="mb-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900" data-testid="aviso-status">
      <AlertTriangle :size="16" class="mt-0.5 shrink-0" /> {{ avisoStatus }}
    </p>

    <!-- 1. O que o cliente aprovou -->
    <section class="mb-6">
      <h3 class="mb-2 text-sm font-bold text-zinc-800">1. O que o cliente aprovou</h3>
      <div v-for="ambiente in detalhe.ambientes" :key="ambiente.id" class="mb-3 rounded-lg border border-zinc-200">
        <div class="flex items-center justify-between border-b border-zinc-100 px-3 py-2">
          <p class="text-sm font-semibold text-zinc-700">{{ ambiente.nome }}</p>
          <div class="flex gap-3 text-xs">
            <button type="button" class="text-brand-primary hover:underline cursor-pointer" @click="marcarAmbiente(ambiente.id, true)">Todos</button>
            <button type="button" class="text-brand-primary hover:underline cursor-pointer" @click="marcarAmbiente(ambiente.id, false)">Nenhum</button>
          </div>
        </div>
        <label
          v-for="movel in ambiente.moveis"
          :key="movel.id"
          class="flex items-center gap-3 px-3 py-2 text-sm"
          :class="semPreco(movel.calculo?.preco_total_centavos) ? 'opacity-60' : 'cursor-pointer'"
          :title="semPreco(movel.calculo?.preco_total_centavos) ? 'Móvel sem preço: complete o móvel no orçamento antes de aprovar.' : undefined"
        >
          <input
            type="checkbox"
            class="accent-brand-primary"
            :checked="marcado(movel.id)"
            :disabled="semPreco(movel.calculo?.preco_total_centavos)"
            :data-testid="`aprovar-movel-${movel.id}`"
            @change="alternar(movel.id)"
          />
          <span class="flex-1 truncate text-zinc-800">{{ movel.nome }}</span>
          <span class="hidden text-xs text-zinc-400 sm:inline">{{ formatarMedidas(movel.largura_mm, movel.altura_mm, movel.profundidade_mm) }}</span>
          <span class="text-xs text-zinc-500">{{ movel.quantidade }}×</span>
          <span v-if="semPreco(movel.calculo?.preco_total_centavos)" class="rounded bg-red-50 px-1.5 text-[10px] font-semibold text-red-700">sem preço</span>
          <span v-else class="w-28 text-right tabular-nums text-zinc-700">{{ formatCurrency(movel.calculo?.preco_total_centavos ?? 0) }}</span>
        </label>
      </div>
      <BaseCheckbox v-if="temInstalacao" v-model="form.incluir_instalacao" :label="`Instalação e montagem (${formatCurrency(detalhe.calculo.instalacao?.preco_centavos ?? 0)})`" />
      <p v-if="erros.movel_ids" class="mt-2 text-xs text-red-600" data-testid="erro-moveis">{{ erros.movel_ids }}</p>
    </section>

    <!-- 2. Valores (todos da API) -->
    <section class="mb-6">
      <h3 class="mb-2 text-sm font-bold text-zinc-800">2. Valores</h3>
      <div class="max-w-sm">
        <CampoPercentualOuValor
          v-model="form.desconto"
          nome="aprovar-desconto"
          rotulo="Desconto"
          :equivalente-centavos="previa?.desconto_centavos ?? null"
          :equivalente-bp="previa?.desconto_bp_efetivo ?? null"
          :erro="erroDesconto"
        />
      </div>
      <dl v-if="previa" class="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:grid-cols-3" :class="isFetching ? 'opacity-50' : ''" data-testid="previa-aprovacao">
        <div><dt class="text-xs text-zinc-500">Bruto</dt><dd class="tabular-nums">{{ formatCurrency(previa.bruto_centavos) }}</dd></div>
        <div><dt class="text-xs text-zinc-500">Desconto</dt><dd class="tabular-nums">− {{ formatCurrency(previa.desconto_centavos) }}</dd></div>
        <div><dt class="text-xs text-zinc-500">Total</dt><dd class="font-bold tabular-nums" data-testid="previa-total">{{ formatCurrency(previa.total_centavos) }}</dd></div>
        <div><dt class="text-xs text-zinc-500">Sinal combinado ({{ formatarBp(previa.sinal_bp_efetivo) }})</dt><dd class="tabular-nums">{{ formatCurrency(previa.sinal_centavos) }}</dd></div>
        <div><dt class="text-xs text-zinc-500">Saldo</dt><dd class="tabular-nums">{{ formatCurrency(previa.saldo_centavos) }}</dd></div>
        <div>
          <dt class="text-xs text-zinc-500">Previsão de entrega</dt>
          <dd>{{ formatDataPura(previa.previsao_entrega) }} ({{ detalhe.parametros.prazo_entrega_dias }} dias)</dd>
        </div>
        <div v-if="previa.margem_liquida_centavos != null" class="col-span-2 sm:col-span-3">
          <dt class="text-xs text-zinc-500">Margem líquida</dt>
          <dd class="tabular-nums" :class="previa.margem_liquida_centavos < 0 ? 'text-red-600' : 'text-emerald-700'">
            {{ formatCurrency(previa.margem_liquida_centavos) }} ({{ formatarBp(previa.margem_liquida_bp ?? 0) }})
          </dd>
        </div>
      </dl>
      <p v-else-if="isFetching" class="mt-3 text-sm text-zinc-400">Calculando…</p>
      <p v-if="erroGeralPrevia" class="mt-2 text-xs text-red-600">{{ erroGeralPrevia }}</p>
    </section>

    <!-- 3. Sinal (O7a): pergunta obrigatória, sem resposta marcada -->
    <section v-if="temSinal" data-testid="bloco-sinal">
      <h3 class="mb-2 text-sm font-bold text-zinc-800">3. Sinal</h3>
      <fieldset class="flex flex-wrap items-center gap-4 text-sm">
        <legend class="mb-2 text-zinc-700">O cliente já pagou o sinal?</legend>
        <label class="flex items-center gap-2"><input v-model="form.sinal_recebido" type="radio" :value="true" class="accent-brand-primary" data-testid="sinal-sim" /> Sim, recebi</label>
        <label class="flex items-center gap-2"><input v-model="form.sinal_recebido" type="radio" :value="false" class="accent-brand-primary" data-testid="sinal-nao" /> Ainda não</label>
      </fieldset>
      <p v-if="tentouAprovar && form.sinal_recebido === null" class="mt-1 text-xs text-red-600">Diga se o sinal já foi pago.</p>

      <div v-if="form.sinal_recebido === true" class="mt-3 flex flex-wrap items-end gap-4">
        <div class="w-40"><MoneyInput v-model="valorRecebidoReais" label="Valor recebido" /></div>
        <div v-if="!form.usar_credito_cliente" class="w-56">
          <BaseSelect v-model="forma" label="Forma de pagamento" required :options="opcoesForma" :error="erros.forma_pagamento_id" placeholder="Escolha" />
        </div>
        <BaseCheckbox v-if="credito > 0" v-model="form.usar_credito_cliente" :label="`Usar crédito do cliente (${formatCurrency(credito)} disponível)`" />
      </div>
      <p v-else-if="form.sinal_recebido === false" class="mt-3 text-sm text-zinc-600" data-testid="sinal-depois">
        O sinal combinado de {{ formatCurrency(sinalCombinado) }} fica registrado no orçamento. Quando o cliente pagar, lance no <strong>Adiantamento</strong> da OS.
      </p>
    </section>

    <template #footer>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="pedirFechar">Cancelar</BaseButton>
        <BaseButton variant="primary" :disabled="!podeAprovar" :is-loading="gravando" data-testid="confirmar-aprovacao" @click="confirmar">
          Aprovar e gerar OS
        </BaseButton>
      </div>
    </template>
  </BaseModal>

  <BaseConfirmModal
    :is-open="perguntandoDescarte"
    title="Descartar a aprovação?"
    description="As escolhas feitas aqui serão perdidas."
    confirm-label="Descartar"
    variant="warning"
    overlay
    @close="perguntandoDescarte = false"
    @confirm="perguntandoDescarte = false; emit('close')"
  />
</template>
