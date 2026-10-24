<script setup lang="ts">
/**
 * @component MovelModal
 * @description Criar ou editar um móvel (Spec 06B §6.4, D23-D30).
 *
 * - NÃO salva sozinho: Cancelar, Salvar e, ao criar, "Salvar e adicionar
 *   outro" (mantém o ambiente, limpa o resto). Fechar com alterações pergunta.
 * - Medidas em milímetros; quantidade de insumo com até 3 casas.
 * - Prévia do preço no rodapé, calculada pela API 400 ms depois da última
 *   tecla (D6). Se a prévia falhar, mostra "Prévia indisponível" e deixa salvar.
 * - Sem `view_custos`: somem mão de obra, valor da central e custos (D16), e
 *   salvar NÃO apaga o que o dono lançou (as chaves de custo nem vão, 06A D24a).
 *
 * Quem grava é o editor (função `salvar` recebida por prop): o modal só monta
 * o móvel e espera a resposta.
 */
import { computed, nextTick, ref, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { onKeyStroke } from '@vueuse/core';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseConfirmModal from '@/shared/components/commons/BaseConfirmModal/BaseConfirmModal.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseTextarea from '@/shared/components/ui/BaseInput/BaseTextarea.vue';
import MoneyInput from '@/shared/components/ui/BaseMoneyInput/MoneyInput.vue';
import { getFornecedores } from '@/modules/products/suppliers/services/fornecedor.service';
import { useFornecedorModal } from '@/modules/products/suppliers/composables/useFornecedorModal';
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';
import { formatCurrency } from '@/shared/utils/finance';

import { CHAVE_RAIZ, LIMITES } from '../../constants/orcamento.constants';
import { useSimularMovel } from '../../composables/useSimularMovel';
import type { MovelDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import { movelFormSchema, movelParaForm, movelVazio, paraApiMovel, type MovelForm } from '../../schemas/movelForm.schema';
import type { MovelEntrada } from '../../services/orcamentoMovel.service';
import InsumoRapidoModal from './InsumoRapidoModal.vue';
import ProdutoAcabadoCampo from '@/modules/marcenaria/shared/components/ProdutoAcabadoCampo.vue';
import { useConfiguracaoMarcenariaQuery } from '@/modules/configuracoes/composables/queries/useConfiguracaoMarcenariaQuery';
import InsumosEditor from './InsumosEditor.vue';

/** O que o editor recebe para gravar. */
export interface MovelParaSalvar {
  movel: MovelEntrada;
  movelId: number | null;
  ambienteId: number;
}

const props = defineProps<{
  isOpen: boolean;
  orcamentoId: number | null;
  ambienteId: number;
  /** Móvel gravado sendo editado; ausente = móvel novo. */
  movel?: MovelDetalhe | null;
  ambientes: { id: number; nome: string }[];
  incluiCustos: boolean;
  /** Custo/hora DESTE orçamento (só quem vê custos), para a linha da mão de obra. */
  custoHoraCentavos: number | null;
  editavel: boolean;
  podeCadastrarInsumo: boolean;
  /**
   * Pode cadastrar fornecedor? Com true, a lista "Central parceira" ganha
   * "+ Cadastrar central parceira" (remodelação item 5). Opcional: sem ela, nada muda.
   */
  podeCadastrarCentral?: boolean;
  /** Grava pelo editor; devolve true se deu certo. */
  salvar: (dados: MovelParaSalvar) => Promise<boolean>;
}>();

const emit = defineEmits<{ close: [] }>();

// --- Formulário ------------------------------------------------------------------
const form = ref<MovelForm>(movelVazio(props.ambienteId));
let original = '';                                         // para saber se houve mudança
const erros = ref<Record<string, string>>({});
const errosInsumos = ref<Record<number, string>>({});
const tentouSalvar = ref(false);
const gravando = ref(false);
const campoNome = ref<InstanceType<typeof BaseInput> | null>(null);

/** Começa do zero (ou do móvel gravado) a cada abertura. */
function preencher() {
  form.value = props.movel ? movelParaForm(props.movel) : movelVazio(props.ambienteId);
  original = JSON.stringify(form.value);
  erros.value = {};
  errosInsumos.value = {};
  tentouSalvar.value = false;
}
// `immediate`: também quando o modal já nasce aberto.
watch(() => props.isOpen, async (aberto) => {
  if (!aberto) return;
  preencher();
  await nextTick();
  (campoNome.value?.$el as HTMLElement | undefined)?.querySelector('input')?.focus();   // foco no "Nome" (§7.12)
}, { immediate: true });

const mudou = computed(() => JSON.stringify(form.value) !== original);
const criando = computed(() => !props.movel);
const titulo = computed(() => (criando.value ? 'Novo móvel' : props.editavel ? 'Editar móvel' : 'Móvel'));
/** O ambiente vai no subtítulo do modal ("Ambiente: Cozinha Gourmet"). */
const subtitulo = computed(() => {
  const ambiente = props.ambientes.find((a) => a.id === form.value.ambiente_id)?.nome;
  return ambiente ? `Ambiente: ${ambiente}` : undefined;
});

/** Classes do card de opção (Produção): borda azul no escolhido, como no design. */
const classeOpcao = (ativa: boolean) => [
  'flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition-colors',
  ativa ? 'border-2 border-brand-primary bg-brand-primary-light' : 'border-zinc-200 bg-white hover:border-zinc-300',
];

/** Título de cada seção numerada do modal. */
const CLASSE_SECAO = 'flex items-center gap-2.5 text-sm font-semibold text-zinc-900';
const CLASSE_NUMERO = 'flex h-6 w-6 items-center justify-center rounded-lg bg-brand-primary-light text-xs font-bold text-brand-primary';
const OPCOES_MAO_OBRA = [
  { valor: 'NENHUMA', rotulo: 'Sem mão de obra' },
  { valor: 'FIXA', rotulo: 'Valor fixo' },
  { valor: 'HORAS', rotulo: 'Horas' },
] as const;

/** Valida com as regras do backend; erros por campo e por linha de insumo. */
function validar(): boolean {
  const resultado = movelFormSchema.safeParse(form.value);
  erros.value = {};
  errosInsumos.value = {};
  if (resultado.success) return true;
  for (const issue of resultado.error.issues) {
    const [campo, indice] = issue.path;
    if (campo === 'insumos' && typeof indice === 'number') errosInsumos.value[indice] = issue.message;
    else erros.value[String(campo)] = issue.message;
  }
  return false;
}
watch(form, () => { if (tentouSalvar.value) validar(); }, { deep: true });

// --- Campos com conversão (o formulário guarda números) ---------------------------
/** Medidas e quantidade: o BaseInput `.number` devolve null quando vazio. */
const medida = (chave: 'largura_mm' | 'altura_mm' | 'profundidade_mm') => computed({
  get: () => form.value[chave] ?? '',
  set: (valor: number | string | null) => { form.value[chave] = valor === '' || valor == null ? null : Number(valor); },
});
const largura = medida('largura_mm');
const altura = medida('altura_mm');
const profundidade = medida('profundidade_mm');
const quantidade = computed({
  get: () => form.value.quantidade,
  set: (valor: number | string | null) => { form.value.quantidade = valor === '' || valor == null ? 0 : Number(valor); },
});
const horas = computed({
  get: () => form.value.mao_obra_horas,
  set: (valor: number | string | null) => { form.value.mao_obra_horas = valor === '' || valor == null ? 0 : Number(valor); },
});
/** Campos de dinheiro: apagar tudo vira R$ 0,00 (nunca "vazio" no formulário). */
const valorCentral = computed({
  get: () => form.value.terceirizado_reais,
  set: (reais: number | null | undefined) => { form.value.terceirizado_reais = reais ?? 0; },
});
const valorMaoObra = computed({
  get: () => form.value.mao_obra_reais,
  set: (reais: number | null | undefined) => { form.value.mao_obra_reais = reais ?? 0; },
});
const ambienteSelecionado = computed({
  get: () => form.value.ambiente_id,
  set: (valor: string | number | undefined) => { if (valor != null && valor !== '') form.value.ambiente_id = Number(valor); },
});
const opcoesAmbiente = computed(() => props.ambientes.map((a) => ({ value: a.id, label: a.nome })));

// --- Central parceira (terceirizado, D29) ---------------------------------------------
const terceirizado = computed(() => form.value.tipo_producao === 'TERCEIRIZADA');

// Faturamento dos móveis (D3): o "tipo fiscal" só aparece com o faturamento ligado.
const { data: configMarcenaria } = useConfiguracaoMarcenariaQuery();
const faturamentoLigado = computed(
  () => !!configMarcenaria.value && configMarcenaria.value.faturamento_modo !== 'DESLIGADO',
);
const { data: fornecedores, refetch: recarregarCentrais } = useQuery({
  queryKey: [CHAVE_RAIZ, 'centrais'],
  queryFn: () => getFornecedores(),
  enabled: computed(() => props.isOpen && terceirizado.value),   // só busca quando precisa
  retry: false,                                                   // 403 não melhora repetindo
});

/** Valor "de mentira" da opção que abre o cadastro (nenhum fornecedor tem esse id). */
const NOVA_CENTRAL = 'nova-central';
/**
 * A central que acabou de ser cadastrada (remodelação item 5). Ela entra na
 * lista na hora, sem esperar a lista de fornecedores ser buscada de novo.
 */
const centralCriada = ref<{ value: number; label: string } | null>(null);

const opcoesCentral = computed(() => {
  const lista: { value: number | string; label: string }[] = (fornecedores.value ?? [])
    .filter((f) => f.ativo)
    .map((f) => ({ value: f.id, label: f.nome }));
  const atual = props.movel?.central;
  // A central gravada aparece mesmo que a lista não carregue (sem permissão de fornecedores).
  if (atual && !lista.some((o) => o.value === atual.fornecedor_id)) lista.unshift({ value: atual.fornecedor_id, label: atual.nome });
  // A recém-cadastrada também, enquanto a lista nova não chega.
  const criada = centralCriada.value;
  if (criada && !lista.some((o) => o.value === criada.value)) lista.push(criada);
  // Por último, o atalho para cadastrar (só para quem pode cadastrar fornecedor).
  if (props.podeCadastrarCentral) lista.push({ value: NOVA_CENTRAL, label: '+ Cadastrar central parceira' });
  return lista;
});

// O cadastro de fornecedor é o mesmo do "Cadastrar arquiteto" (Spec 09B D5).
const { openCreateModalWithCallback } = useFornecedorModal();

const central = computed({
  get: () => form.value.central_fornecedor_id ?? undefined,
  set: (valor: string | number | undefined) => {
    if (valor === NOVA_CENTRAL) {
      // Escolheu "+ Cadastrar central parceira": abre o cadastro e NÃO muda a central ainda.
      // Quando o fornecedor nascer, ele vira a central escolhida.
      openCreateModalWithCallback('produto', (novo) => {
        centralCriada.value = { value: novo.id, label: novo.nome };
        form.value.central_fornecedor_id = novo.id;
        void recarregarCentrais();                      // a lista passa a ter a central nova
      });
      return;
    }
    form.value.central_fornecedor_id = valor == null || valor === '' ? null : Number(valor);
  },
});

// --- Prévia (D6, D30) ---------------------------------------------------------------
const { data: previa, isFetching: carregandoPrevia, isError: previaFalhou } = useSimularMovel(
  computed(() => (props.isOpen ? props.orcamentoId : null)),
  form,
  computed(() => props.movel?.id ?? null),
  computed(() => props.incluiCustos),
);

/** Custo/hora do orçamento zerado: a mão de obra por horas sai zerada (D28). */
const custoHoraZerado = computed(() => (props.custoHoraCentavos ?? 0) === 0);

// --- Cadastro rápido de insumo (D31) ------------------------------------------------
const editorInsumos = ref<InstanceType<typeof InsumosEditor> | null>(null);
const cadastroAberto = ref(false);
const nomeParaCadastro = ref('');
function abrirCadastro(nome: string) {
  nomeParaCadastro.value = nome;
  cadastroAberto.value = true;
}
/** O produto recém-cadastrado entra no móvel na hora. */
function aoCadastrar(produto: ProdutoRead) {
  void editorInsumos.value?.incluir(produto);
}

// --- Salvar e fechar ----------------------------------------------------------------
async function gravar(continuar: boolean) {
  tentouSalvar.value = true;
  if (!validar()) return;
  gravando.value = true;
  try {
    const ok = await props.salvar({
      movel: paraApiMovel(form.value, props.incluiCustos),
      movelId: props.movel?.id ?? null,
      ambienteId: form.value.ambiente_id,
    });
    if (!ok) return;                                       // o erro já apareceu (toast do editor)
    if (continuar) {
      // "Salvar e adicionar outro": mantém o ambiente, limpa o resto (D23).
      form.value = movelVazio(form.value.ambiente_id);
      original = JSON.stringify(form.value);
      tentouSalvar.value = false;
      erros.value = {};
      await nextTick();
      (campoNome.value?.$el as HTMLElement | undefined)?.querySelector('input')?.focus();
    } else {
      emit('close');
    }
  } finally {
    gravando.value = false;
  }
}

// Fechar com alterações pergunta antes (D23).
const perguntandoDescarte = ref(false);
function pedirFechar() {
  if (props.editavel && mudou.value) perguntandoDescarte.value = true;
  else emit('close');
}
function descartar() {
  perguntandoDescarte.value = false;
  emit('close');
}

// `Esc` fecha (com a pergunta, se houver mudança). Ignora quando outro modal está por cima.
onKeyStroke('Escape', () => {
  if (props.isOpen && !cadastroAberto.value && !perguntandoDescarte.value) pedirFechar();
});
</script>

<template>
  <BaseModal :is-open="isOpen" :title="titulo" :subtitle="subtitulo" size="xl" @close="pedirFechar">
    <fieldset :disabled="!editavel" class="flex flex-col divide-y divide-zinc-100">
      <!-- 1. Identificação -->
      <section class="flex flex-col gap-4 pb-6">
        <h3 :class="CLASSE_SECAO"><span :class="CLASSE_NUMERO">1</span>Identificação</h3>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-[minmax(0,1fr)_10rem]">
          <BaseInput ref="campoNome" v-model="form.nome" label="Nome do móvel" required :error="erros.nome" data-testid="movel-nome" />
          <BaseInput v-model.number="quantidade" type="number" label="Quantidade" min="1" step="1" required :error="erros.quantidade" />
        </div>
        <div>
          <BaseTextarea v-model="form.descricao" label="Descrição" :rows="2" :error="erros.descricao" placeholder="Ex.: MDF Branco TX e Freijó, corrediças com amortecedor" />
          <p class="mt-1 text-xs text-zinc-500">Sai na proposta. Até {{ LIMITES.descricaoMovel }} caracteres.</p>
        </div>
        <!-- Ambiente: só ao editar (mover o móvel de ambiente, 06A §6.1) -->
        <div v-if="!criando && ambientes.length > 1" class="max-w-xs">
          <BaseSelect v-model="ambienteSelecionado" label="Ambiente" :options="opcoesAmbiente" />
        </div>
      </section>

      <!-- 2. Dimensões (mm, D24). O "mm" também aparece dentro de cada campo (remodelação item 4). -->
      <section class="flex flex-col gap-4 py-6">
        <div class="flex items-center justify-between">
          <h3 :class="CLASSE_SECAO"><span :class="CLASSE_NUMERO">2</span>Dimensões</h3>
          <span class="text-xs text-zinc-500">em milímetros</span>
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <BaseInput v-model.number="largura" type="number" label="Largura (L)" min="1" step="1" sufixo="mm" :error="erros.largura_mm" />
          <BaseInput v-model.number="altura" type="number" label="Altura (A)" min="1" step="1" sufixo="mm" :error="erros.altura_mm" />
          <BaseInput v-model.number="profundidade" type="number" label="Profundidade (P)" min="1" step="1" sufixo="mm" :error="erros.profundidade_mm" />
        </div>
      </section>

      <!-- 3. Produção (D29) -->
      <section class="flex flex-col gap-4 py-6">
        <h3 :class="CLASSE_SECAO"><span :class="CLASSE_NUMERO">3</span>Produção</h3>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2" role="radiogroup" aria-label="Tipo de produção">
          <label :class="classeOpcao(form.tipo_producao === 'INTERNA')">
            <input v-model="form.tipo_producao" type="radio" value="INTERNA" class="mt-0.5 h-4 w-4 accent-brand-primary" />
            <span>
              <span class="block text-sm font-semibold text-zinc-900">Produção interna</span>
              <span class="text-xs text-zinc-500">Corte, borda e montagem na marcenaria própria.</span>
            </span>
          </label>
          <label :class="classeOpcao(terceirizado)">
            <input v-model="form.tipo_producao" type="radio" value="TERCEIRIZADA" class="mt-0.5 h-4 w-4 accent-brand-primary" data-testid="producao-terceirizada" />
            <span>
              <span class="block text-sm font-semibold text-zinc-900">Terceirizada</span>
              <span class="text-xs text-zinc-500">As peças vêm prontas de uma central parceira.</span>
            </span>
          </label>
        </div>
        <div v-if="terceirizado" class="grid grid-cols-1 gap-4 rounded-xl border border-amber-200 bg-amber-50 p-4 md:grid-cols-[minmax(0,1fr)_12rem]">
          <BaseSelect v-model="central" label="Central parceira" required :options="opcoesCentral" :error="erros.central_fornecedor_id" placeholder="Escolha a central" />
          <div v-if="incluiCustos" data-testid="valor-central">
            <MoneyInput v-model="valorCentral" label="Valor da central" :error="erros.terceirizado_reais" />
          </div>
        </div>
        <p v-if="erros.central_fornecedor_id" class="text-xs text-red-600" data-testid="erro-central">{{ erros.central_fornecedor_id }}</p>
        <!-- Faturamento (D3): o produto acabado que este móvel vira na NF-e. -->
        <div v-if="faturamentoLigado" class="rounded-xl border border-zinc-200 p-4" data-testid="tipo-fiscal">
          <ProdutoAcabadoCampo
            v-model="form.produto_acabado_id"
            rotulo="Tipo fiscal na nota"
            :ajuda="terceirizado ? 'Sem escolha, sai como o produto do móvel comprado pronto.' : 'Sem escolha, sai como o produto do móvel fabricado.'"
            texto-vazio="O padrão da configuração"
            :disabled="!editavel"
            sem-divisoria
          />
        </div>
      </section>

      <!-- 4. Insumos (D25-D27) -->
      <section class="flex flex-col gap-4 py-6">
        <h3 :class="CLASSE_SECAO"><span :class="CLASSE_NUMERO">4</span>Insumos</h3>
        <InsumosEditor
          ref="editorInsumos"
          v-model="form.insumos"
          :inclui-custos="incluiCustos"
          :editavel="editavel"
          :pode-cadastrar="podeCadastrarInsumo"
          :erros="errosInsumos"
          @cadastrar="abrirCadastro"
        />
        <p v-if="erros.insumos" class="text-xs text-red-600">{{ erros.insumos }}</p>
      </section>

      <!-- 5. Mão de obra (C4, D28): só quem vê custos -->
      <section class="flex flex-col gap-4 py-6">
        <h3 :class="CLASSE_SECAO"><span :class="CLASSE_NUMERO">5</span>Mão de obra <span class="text-xs font-normal text-zinc-500">por unidade</span></h3>
        <fieldset v-if="incluiCustos" data-testid="mao-obra">
          <legend class="sr-only">Mão de obra (por unidade)</legend>
          <div class="flex flex-wrap items-end gap-4">
            <div class="flex rounded-xl border border-zinc-200 bg-white p-1" role="radiogroup" aria-label="Como cobrar a mão de obra">
              <label
                v-for="opcao in OPCOES_MAO_OBRA"
                :key="opcao.valor"
                :class="['flex min-h-9 cursor-pointer items-center rounded-lg px-3 text-xs font-semibold', form.mao_obra_modo === opcao.valor ? 'bg-zinc-900 text-white' : 'text-zinc-600 hover:bg-zinc-50']"
              >
                <input v-model="form.mao_obra_modo" type="radio" :value="opcao.valor" class="sr-only" />
                {{ opcao.rotulo }}
              </label>
            </div>
            <div v-if="form.mao_obra_modo === 'FIXA'" class="w-40">
              <MoneyInput v-model="valorMaoObra" label="Valor" />
            </div>
            <div v-if="form.mao_obra_modo === 'HORAS'" class="w-28">
              <BaseInput v-model.number="horas" type="number" label="Horas" min="0" step="0.25" />
            </div>
            <p v-if="form.mao_obra_modo === 'HORAS'" class="pb-3 text-xs text-zinc-500">
              × {{ formatCurrency(custoHoraCentavos ?? 0) }}/h (custo/hora deste orçamento)
            </p>
          </div>
          <p v-if="form.mao_obra_modo === 'HORAS' && custoHoraZerado" class="mt-2 text-xs text-amber-700" data-testid="aviso-hora-zero">
            O custo/hora deste orçamento está em R$ 0,00; a mão de obra por horas sairá zerada.
          </p>
        </fieldset>
        <p v-else class="text-sm text-zinc-500" data-testid="frase-sem-custos">
          Mão de obra, valor da central e custos são preenchidos por quem vê os custos.
        </p>
      </section>

      <!-- 6. Prévia (D30): números da API; esmaecidos enquanto recalcula -->
      <section class="flex flex-col gap-4 pt-6">
        <h3 :class="CLASSE_SECAO"><span :class="CLASSE_NUMERO">6</span>Prévia de custo e preço</h3>
        <div :class="carregandoPrevia ? 'opacity-50' : ''" data-testid="previa">
          <p v-if="previaFalhou && !previa" class="text-sm text-zinc-500">Prévia indisponível</p>
          <div v-else-if="previa" class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div v-if="incluiCustos && previa.calculo.custo_unit_centavos != null" class="rounded-xl border border-zinc-200 p-4">
              <p class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Custo unitário</p>
              <p class="mt-1 text-xl font-extrabold tabular-nums text-zinc-900">{{ formatCurrency(previa.calculo.custo_unit_centavos) }}</p>
            </div>
            <div class="rounded-xl border border-zinc-200 p-4">
              <p class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Preço unitário</p>
              <p class="mt-1 text-xl font-extrabold tabular-nums text-zinc-900">{{ formatCurrency(previa.calculo.preco_unit_centavos) }}</p>
            </div>
            <div class="rounded-xl border-2 border-brand-primary bg-brand-primary-light p-4">
              <p class="text-xs font-semibold uppercase tracking-wider text-brand-primary">Preço total</p>
              <p class="mt-1 text-xl font-extrabold tabular-nums text-brand-primary" data-testid="previa-total">{{ formatCurrency(previa.calculo.preco_total_centavos) }}</p>
            </div>
          </div>
          <p v-else class="text-sm text-zinc-500">A prévia aparece quando o nome e a quantidade estiverem preenchidos.</p>
        </div>
      </section>
    </fieldset>

    <template #footer>
      <div class="flex flex-wrap justify-end gap-3">
        <BaseButton variant="secondary" @click="pedirFechar">{{ editavel ? 'Cancelar' : 'Fechar' }}</BaseButton>
        <template v-if="editavel">
          <BaseButton v-if="criando" variant="ghost" :is-loading="gravando" data-testid="salvar-e-outro" @click="gravar(true)">
            Salvar e adicionar outro
          </BaseButton>
          <BaseButton variant="primary" :is-loading="gravando" data-testid="salvar-movel" @click="gravar(false)">Salvar móvel</BaseButton>
        </template>
      </div>
    </template>
  </BaseModal>

  <InsumoRapidoModal :is-open="cadastroAberto" :nome-inicial="nomeParaCadastro" @close="cadastroAberto = false" @criado="aoCadastrar" />

  <BaseConfirmModal
    :is-open="perguntandoDescarte"
    title="Descartar alterações"
    description="Descartar as alterações deste móvel?"
    confirm-label="Descartar"
    variant="warning"
    overlay
    @close="perguntandoDescarte = false"
    @confirm="descartar"
  />
</template>
