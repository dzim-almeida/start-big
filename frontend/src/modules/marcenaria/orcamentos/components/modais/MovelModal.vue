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
import type { ProdutoRead } from '@/modules/products/inventory/types/products.types';
import { formatCurrency } from '@/shared/utils/finance';

import { CHAVE_RAIZ, LIMITES } from '../../constants/orcamento.constants';
import { useSimularMovel } from '../../composables/useSimularMovel';
import type { MovelDetalhe } from '../../schemas/orcamentoDetalhe.schema';
import { movelFormSchema, movelParaForm, movelVazio, paraApiMovel, type MovelForm } from '../../schemas/movelForm.schema';
import type { MovelEntrada } from '../../services/orcamentoMovel.service';
import InsumoRapidoModal from './InsumoRapidoModal.vue';
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
const titulo = computed(() => {
  const ambiente = props.ambientes.find((a) => a.id === form.value.ambiente_id)?.nome;
  const base = criando.value ? 'Novo móvel' : props.editavel ? 'Editar móvel' : 'Móvel';
  return ambiente ? `${base} — ${ambiente}` : base;
});

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
const { data: fornecedores } = useQuery({
  queryKey: [CHAVE_RAIZ, 'centrais'],
  queryFn: () => getFornecedores(),
  enabled: computed(() => props.isOpen && terceirizado.value),   // só busca quando precisa
  retry: false,                                                   // 403 não melhora repetindo
});
const opcoesCentral = computed(() => {
  const lista = (fornecedores.value ?? []).filter((f) => f.ativo).map((f) => ({ value: f.id, label: f.nome }));
  const atual = props.movel?.central;
  // A central gravada aparece mesmo que a lista não carregue (sem permissão de fornecedores).
  if (atual && !lista.some((o) => o.value === atual.fornecedor_id)) lista.unshift({ value: atual.fornecedor_id, label: atual.nome });
  return lista;
});
const central = computed({
  get: () => form.value.central_fornecedor_id ?? undefined,
  set: (valor: string | number | undefined) => { form.value.central_fornecedor_id = valor == null || valor === '' ? null : Number(valor); },
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
  <BaseModal :is-open="isOpen" :title="titulo" size="xl" @close="pedirFechar">
    <fieldset :disabled="!editavel" class="flex flex-col gap-5">
      <!-- Nome e descrição -->
      <div class="grid grid-cols-1 gap-4">
        <BaseInput ref="campoNome" v-model="form.nome" label="Nome" required :error="erros.nome" data-testid="movel-nome" />
        <div>
          <BaseTextarea v-model="form.descricao" label="Descrição" :rows="2" :error="erros.descricao" placeholder="Ex.: MDF Branco TX e Freijó, corrediças com amortecedor" />
          <p class="mt-1 text-[11px] text-zinc-400">Sai na proposta. Até {{ LIMITES.descricaoMovel }} caracteres.</p>
        </div>
      </div>

      <!-- Medidas (mm) e quantidade (D24) -->
      <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
        <BaseInput v-model.number="largura" type="number" label="Largura (mm)" min="1" step="1" :error="erros.largura_mm" />
        <BaseInput v-model.number="altura" type="number" label="Altura (mm)" min="1" step="1" :error="erros.altura_mm" />
        <BaseInput v-model.number="profundidade" type="number" label="Profundidade (mm)" min="1" step="1" :error="erros.profundidade_mm" />
        <BaseInput v-model.number="quantidade" type="number" label="Quantidade" min="1" step="1" required :error="erros.quantidade" />
      </div>

      <!-- Ambiente: só ao editar (mover o móvel de ambiente, 06A §6.1) -->
      <div v-if="!criando && ambientes.length > 1" class="max-w-xs">
        <BaseSelect v-model="ambienteSelecionado" label="Ambiente" :options="opcoesAmbiente" />
      </div>

      <!-- Produção (D29) -->
      <fieldset>
        <legend class="mb-2 text-xs font-medium text-zinc-600">Produção</legend>
        <div class="flex flex-wrap items-end gap-4">
          <label class="flex items-center gap-2 text-sm">
            <input v-model="form.tipo_producao" type="radio" value="INTERNA" class="accent-brand-primary" /> Interna
          </label>
          <label class="flex items-center gap-2 text-sm">
            <input v-model="form.tipo_producao" type="radio" value="TERCEIRIZADA" class="accent-brand-primary" data-testid="producao-terceirizada" /> Terceirizada
          </label>
          <template v-if="terceirizado">
            <div class="w-64">
              <BaseSelect v-model="central" label="Central parceira" required :options="opcoesCentral" :error="erros.central_fornecedor_id" placeholder="Escolha a central" />
            </div>
            <div v-if="incluiCustos" class="w-40" data-testid="valor-central">
              <MoneyInput v-model="valorCentral" label="Valor da central" :error="erros.terceirizado_reais" />
            </div>
          </template>
        </div>
        <p v-if="erros.central_fornecedor_id" class="mt-1 text-[11px] text-red-600" data-testid="erro-central">{{ erros.central_fornecedor_id }}</p>
      </fieldset>

      <!-- Insumos (D25-D27) -->
      <InsumosEditor
        ref="editorInsumos"
        v-model="form.insumos"
        :inclui-custos="incluiCustos"
        :editavel="editavel"
        :pode-cadastrar="podeCadastrarInsumo"
        :erros="errosInsumos"
        @cadastrar="abrirCadastro"
      />
      <p v-if="erros.insumos" class="text-[11px] text-red-600">{{ erros.insumos }}</p>

      <!-- Mão de obra (C4, D28): só quem vê custos -->
      <fieldset v-if="incluiCustos" data-testid="mao-obra">
        <legend class="mb-2 text-xs font-medium text-zinc-600">Mão de obra (por unidade)</legend>
        <div class="flex flex-wrap items-end gap-4">
          <label class="flex items-center gap-2 text-sm">
            <input v-model="form.mao_obra_modo" type="radio" value="NENHUMA" class="accent-brand-primary" /> Sem mão de obra
          </label>
          <label class="flex items-center gap-2 text-sm">
            <input v-model="form.mao_obra_modo" type="radio" value="FIXA" class="accent-brand-primary" /> Valor fixo
          </label>
          <label class="flex items-center gap-2 text-sm">
            <input v-model="form.mao_obra_modo" type="radio" value="HORAS" class="accent-brand-primary" /> Horas
          </label>
          <div v-if="form.mao_obra_modo === 'FIXA'" class="w-40">
            <MoneyInput v-model="valorMaoObra" label="Valor" />
          </div>
          <div v-if="form.mao_obra_modo === 'HORAS'" class="w-28">
            <BaseInput v-model.number="horas" type="number" label="Horas" min="0" step="0.25" />
          </div>
        </div>
        <p v-if="form.mao_obra_modo === 'HORAS'" class="mt-2 text-xs text-zinc-500">
          Custo/hora deste orçamento: {{ formatCurrency(custoHoraCentavos ?? 0) }}
        </p>
        <p v-if="form.mao_obra_modo === 'HORAS' && custoHoraZerado" class="mt-1 text-xs text-amber-700" data-testid="aviso-hora-zero">
          O custo/hora deste orçamento está em R$ 0,00; a mão de obra por horas sairá zerada.
        </p>
      </fieldset>
      <p v-else class="text-xs text-zinc-500" data-testid="frase-sem-custos">
        Mão de obra, valor da central e custos são preenchidos por quem vê os custos.
      </p>
    </fieldset>

    <template #footer>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <!-- Prévia (D30): números da API; esmaecidos enquanto recalcula -->
        <div class="flex flex-wrap gap-x-5 gap-y-1 text-sm" :class="carregandoPrevia ? 'opacity-50' : ''" data-testid="previa">
          <template v-if="previaFalhou && !previa">
            <span class="text-zinc-400">Prévia indisponível</span>
          </template>
          <template v-else-if="previa">
            <span v-if="incluiCustos && previa.calculo.custo_unit_centavos != null" class="text-zinc-500">
              Custo unitário <strong class="tabular-nums text-zinc-700">{{ formatCurrency(previa.calculo.custo_unit_centavos) }}</strong>
            </span>
            <span class="text-zinc-500">
              Preço unitário <strong class="tabular-nums text-zinc-800">{{ formatCurrency(previa.calculo.preco_unit_centavos) }}</strong>
            </span>
            <span class="text-zinc-500">
              Total <strong class="tabular-nums text-zinc-900" data-testid="previa-total">{{ formatCurrency(previa.calculo.preco_total_centavos) }}</strong>
            </span>
          </template>
          <span v-else class="text-zinc-400">A prévia aparece quando o nome e a quantidade estiverem preenchidos.</span>
        </div>

        <div class="flex gap-2">
          <BaseButton variant="secondary" @click="pedirFechar">{{ editavel ? 'Cancelar' : 'Fechar' }}</BaseButton>
          <template v-if="editavel">
            <BaseButton v-if="criando" variant="secondary" :is-loading="gravando" data-testid="salvar-e-outro" @click="gravar(true)">
              Salvar e adicionar outro
            </BaseButton>
            <BaseButton variant="primary" :is-loading="gravando" data-testid="salvar-movel" @click="gravar(false)">Salvar</BaseButton>
          </template>
        </div>
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
