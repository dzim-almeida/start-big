// ============================================================================
// COMPONENTE: ModalMovimentacaoEstoque
// PROJETO: Start Big - Gestão de Hardware
// RESPONSABILIDADE: Registrar entradas, saídas e ajustes de inventário.
// FUNCIONALIDADES: 
//   - Cálculo automático de estoque atual via computed.
//   - Feedback visual dinâmico (Badges) conforme o tipo de operação.
//   - Validação de quantidade mínima e tratamento de erros de API.
// ============================================================================
<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { ArrowDownCircle, ArrowUpCircle, SlidersHorizontal } from 'lucide-vue-next';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import type { SelectOption } from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import { useCreateMovimentacaoMutation } from '../composables/useMovimentacoesQuery';
import type { MovimentacaoTipo, ProdutoRead } from '../types/products.types';
import { formatarQuantidade } from '@/shared/utils/quantidade';
import { storeToRefs } from 'pinia';
import { useConfiguracoesStore } from '@/shared/stores/configuracoes.store';

interface Props {
  isOpen: boolean;
  produtos: ProdutoRead[];
  initialProdutoId?: number;
  initialTipo?: MovimentacaoTipo;
}

const props = defineProps<Props>();
const emit = defineEmits<{ (e: 'close'): void }>();

const mutation = useCreateMovimentacaoMutation();

const produtoId = ref<string>('');
const tipo = ref<MovimentacaoTipo>('ENTRADA');
const quantidade = ref<number | ''>('');
// Valor pago por unidade nesta compra, em reais (vira centavos no envio).
// É este número que recalcula o custo médio do produto — e sem ele o relatório
// de lucro não tem de onde tirar o custo da peça.
const valorPago = ref<string>('');
const observacao = ref('');
const erro = ref('');

// ── Embalagens (fardo/caixa) — só com a chave ligada em Configurações ──
// Entrada: quantidade e valor pago POR EMBALAGEM; o backend converte para a
// unidade. Ajuste: a contagem pode ser feita em fardos + unidades avulsas.
const { usarEmbalagens } = storeToRefs(useConfiguracoesStore());
const embalagemId = ref<string>('');
const contagemEmbalagens = ref<number | ''>('');
const contagemAvulsas = ref<number | ''>('');

// Pré-preenche quando aberto com produto/tipo específico
watch(() => props.isOpen, (open) => {
  if (open) {
    produtoId.value = props.initialProdutoId ? String(props.initialProdutoId) : '';
    tipo.value = props.initialTipo ?? 'ENTRADA';
    quantidade.value = '';
    valorPago.value = '';
    observacao.value = '';
    erro.value = '';
    embalagemId.value = '';
    contagemEmbalagens.value = '';
    contagemAvulsas.value = '';
  }
});

const produtoOptions = computed<SelectOption[]>(() =>
  props.produtos
    .filter((p) => p.ativo)
    .map((p) => ({ value: String(p.id), label: p.nome })),
);

const tipoOptions: SelectOption[] = [
  { value: 'ENTRADA', label: 'Entrada (adicionar ao estoque)' },
  { value: 'SAIDA', label: 'Saída (retirar do estoque)' },
  { value: 'AJUSTE', label: 'Ajuste (definir quantidade final)' },
];

const tipoBadge = computed(() => {
  if (tipo.value === 'ENTRADA') return { icon: ArrowDownCircle, class: 'text-brand-primary bg-brand-primary/10', label: 'Entrada' };
  if (tipo.value === 'SAIDA') return { icon: ArrowUpCircle, class: 'text-red-600 bg-red-50', label: 'Saída' };
  return { icon: SlidersHorizontal, class: 'text-amber-600 bg-amber-50', label: 'Ajuste' };
});

const produtoSelecionado = computed(() =>
  props.produtos.find((p) => String(p.id) === produtoId.value),
);

// Custo que o sistema conhece hoje: a média calculada, ou o preço de referência
// do cadastro enquanto nunca houve compra registrada com valor pago.
const custoConhecido = computed<number | null>(() => {
  const estoque = produtoSelecionado.value?.estoque;
  if (!estoque) return null;
  return estoque.custo_medio ?? estoque.valor_entrada ?? null;
});

// Só a compra recalcula o custo. Numa devolução (que também é entrada), o campo
// fica de fora de propósito: devolver não é comprar, e preencher ali mexeria na
// média sem que nada tenha sido pago.
const pedeValorPago = computed(() => tipo.value === 'ENTRADA');

// Embalagens de verdade (fator ≥ 2) ativas do produto escolhido.
const embalagensDoProduto = computed(() =>
  usarEmbalagens.value ? (produtoSelecionado.value?.embalagens ?? []).filter((e) => e.ativo && e.fator >= 2) : [],
);
const embalagensDeEntrada = computed(() => embalagensDoProduto.value.filter((e) => e.usa_na_entrada));
const embalagemOptions = computed<SelectOption[]>(() => [
  { value: '', label: 'Unidade' },
  ...embalagensDeEntrada.value.map((e) => ({ value: String(e.id), label: `${e.sigla} de ${e.fator}` })),
]);
const embalagemEscolhida = computed(() =>
  tipo.value === 'ENTRADA' ? (embalagensDeEntrada.value.find((e) => String(e.id) === embalagemId.value) ?? null) : null,
);
// Quantas unidades a entrada/saída representa (a embalagem multiplica).
const unidadesDaMovimentacao = computed(() => Number(quantidade.value) * (embalagemEscolhida.value?.fator ?? 1));

// Ajuste por contagem: "10 FD + 3 un" = 123 un. A menor embalagem é a que se conta.
const embalagemDeContagem = computed(() => [...embalagensDoProduto.value].sort((a, b) => a.fator - b.fator)[0] ?? null);
function aplicarContagem() {
  const e = embalagemDeContagem.value;
  if (!e) return;
  const total = (Number(contagemEmbalagens.value) || 0) * e.fator + (Number(contagemAvulsas.value) || 0);
  quantidade.value = total > 0 ? total : '';
}
watch([contagemEmbalagens, contagemAvulsas], aplicarContagem);
watch(produtoId, () => (embalagemId.value = ''));

// Prévia da média resultante — deixa visível, antes de gravar, que comprar mais
// caro não joga o custo todo para o preço novo.
const novaMediaPrevista = computed<number | null>(() => {
  if (!pedeValorPago.value) return null;
  // Com embalagem, o valor digitado é por embalagem: a média é por unidade.
  const fator = embalagemEscolhida.value?.fator ?? 1;
  const pagoDigitado = paraCentavos(valorPago.value);
  const pago = pagoDigitado === undefined ? undefined : Math.round(pagoDigitado / fator);
  const qtd = Number(quantidade.value) * fator;
  if (pago === undefined || !qtd || qtd < 1) return null;

  const anterior = Math.max(0, produtoSelecionado.value?.estoque.quantidade ?? 0);
  const custoAnterior = custoConhecido.value;
  if (custoAnterior == null || anterior === 0) return pago;
  return Math.round((anterior * custoAnterior + qtd * pago) / (anterior + qtd));
});

function paraCentavos(valor: string): number | undefined {
  const limpo = valor.replace(/\s/g, '').replace(',', '.');
  if (!limpo) return undefined;
  const numero = Number(limpo);
  if (!Number.isFinite(numero) || numero < 0) return undefined;
  return Math.round(numero * 100);
}

function formatarMoeda(centavos: number): string {
  return (centavos / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function resetForm() {
  produtoId.value = '';
  tipo.value = 'ENTRADA';
  quantidade.value = '';
  valorPago.value = '';
  observacao.value = '';
  erro.value = '';
}

function handleClose() {
  resetForm();
  emit('close');
}

async function handleSubmit() {
  erro.value = '';

  if (!produtoId.value) { erro.value = 'Selecione um produto.'; return; }
  if (!quantidade.value || Number(quantidade.value) < 1) { erro.value = 'Informe uma quantidade válida (mínimo 1).'; return; }

  const custoUnitario = pedeValorPago.value ? paraCentavos(valorPago.value) : undefined;
  if (pedeValorPago.value && valorPago.value.trim() && custoUnitario === undefined) {
    erro.value = 'Valor pago inválido. Use apenas números (ex: 45,90).';
    return;
  }

  mutation.mutate(
    {
      produto_id: Number(produtoId.value),
      data: {
        tipo: tipo.value,
        quantidade: Number(quantidade.value),
        custo_unitario: custoUnitario,
        observacao: observacao.value.trim() || undefined,
        ...(embalagemEscolhida.value ? { embalagem_id: embalagemEscolhida.value.id } : {}),
      },
    },
    {
      onSuccess: () => handleClose(),
      onError: (err: any) => {
        const detail = err?.response?.data?.detail;
        erro.value = typeof detail === 'string' ? detail : 'Erro ao registrar movimentação.';
      },
    },
  );
}
</script>

<template>
  <BaseModal :is-open="isOpen" title="Nova Movimentação de Estoque" size="md" @close="handleClose">
    <div class="space-y-5">
      <div
        v-if="erro"
        class="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm"
      >
        {{ erro }}
      </div>

      <!-- Produto -->
      <BaseSelect
        v-model="produtoId"
        label="Produto"
        placeholder="Selecione o produto"
        :options="produtoOptions"
        :required="true"
      />

      <!-- Estoque atual -->
      <div
        v-if="produtoSelecionado"
        class="flex items-center gap-2 px-3 py-2 bg-zinc-50 border border-zinc-200 rounded-lg text-sm text-zinc-600"
      >
        <span>Estoque atual:</span>
        <span class="font-semibold text-zinc-800">
          {{ formatarQuantidade(produtoSelecionado.estoque.quantidade, produtoSelecionado.unidade_medida) }}
        </span>
      </div>

      <!-- Tipo -->
      <BaseSelect
        v-model="tipo"
        label="Tipo de Movimentação"
        :options="tipoOptions"
        :required="true"
      />

      <!-- Indicador visual do tipo -->
      <div
        class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium"
        :class="tipoBadge.class"
      >
        <component :is="tipoBadge.icon" :size="16" />
        <span v-if="tipo === 'AJUSTE'">Define a quantidade final do estoque</span>
        <span v-else-if="tipo === 'ENTRADA'">Adiciona ao estoque atual</span>
        <span v-else>Retira do estoque atual</span>
      </div>

      <!-- Entrada por embalagem (só com fardo/caixa cadastrado e a chave ligada) -->
      <BaseSelect
        v-if="tipo === 'ENTRADA' && embalagensDeEntrada.length"
        v-model="embalagemId"
        label="Entrou em"
        :options="embalagemOptions"
      />

      <!-- Ajuste: contar em fardos + avulsas -->
      <div v-if="tipo === 'AJUSTE' && embalagemDeContagem" class="p-3 rounded-lg bg-zinc-50 border border-zinc-200 space-y-2">
        <p class="text-xs font-medium text-zinc-600">Contou em {{ embalagemDeContagem.sigla }}? (opcional)</p>
        <div class="flex items-center gap-2 text-sm text-zinc-600">
          <input
            v-model.number="contagemEmbalagens"
            type="number"
            min="0"
            placeholder="0"
            class="w-20 px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:border-brand-primary"
          />
          <span>{{ embalagemDeContagem.sigla }} de {{ embalagemDeContagem.fator }} +</span>
          <input
            v-model.number="contagemAvulsas"
            type="number"
            min="0"
            placeholder="0"
            class="w-20 px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:border-brand-primary"
          />
          <span>un avulsas</span>
        </div>
      </div>

      <!-- Quantidade -->
      <div>
        <label class="block text-sm font-medium text-zinc-700 mb-1">
          {{ tipo === 'AJUSTE' ? 'Quantidade final desejada' : embalagemEscolhida ? `Quantidade de ${embalagemEscolhida.sigla}` : 'Quantidade' }}
          <span class="text-red-500 ml-0.5">*</span>
        </label>
        <input
          v-model.number="quantidade"
          type="number"
          min="1"
          placeholder="0"
          class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary"
        />
        <p v-if="embalagemEscolhida && Number(quantidade) > 0" class="mt-1.5 text-xs text-zinc-500">
          = <strong class="text-zinc-700">{{ unidadesDaMovimentacao }} un</strong> no estoque
        </p>
      </div>

      <!-- Valor pago (só na entrada: é a compra que muda o custo) -->
      <div v-if="pedeValorPago">
        <label class="block text-sm font-medium text-zinc-700 mb-1">
          Valor pago por {{ embalagemEscolhida ? embalagemEscolhida.sigla : 'unidade' }}
          <span class="text-zinc-400 font-normal">(opcional)</span>
        </label>
        <div class="relative">
          <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-zinc-400">R$</span>
          <input
            v-model="valorPago"
            type="text"
            inputmode="decimal"
            placeholder="0,00"
            class="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary"
          />
        </div>
        <p v-if="novaMediaPrevista !== null" class="mt-1.5 text-xs text-zinc-500">
          Custo médio passa a
          <strong class="text-zinc-700">{{ formatarMoeda(novaMediaPrevista) }}</strong>
          <template v-if="custoConhecido !== null">
            (era {{ formatarMoeda(custoConhecido) }})
          </template>
        </p>
        <p v-else class="mt-1.5 text-xs text-zinc-400">
          Deixe em branco se for devolução — devolver não é comprar, e o custo médio não muda.
        </p>
      </div>

      <!-- Observação -->
      <div>
        <label class="block text-sm font-medium text-zinc-700 mb-1">Observação</label>
        <textarea
          v-model="observacao"
          rows="2"
          placeholder="Motivo da movimentação (opcional)"
          class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm resize-none focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary"
        ></textarea>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-3 w-full">
        <BaseButton type="button" variant="secondary" @click="handleClose">Cancelar</BaseButton>
        <BaseButton
          type="button"
          variant="primary"
          :is-loading="mutation.isPending.value"
          @click="handleSubmit"
        >
          Registrar
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>