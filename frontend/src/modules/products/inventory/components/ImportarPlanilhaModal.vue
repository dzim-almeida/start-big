<script setup lang="ts">
/**
 * Cadastro de vários produtos por uma planilha Excel.
 *
 * Três passos: escolher o arquivo → conferir → resumo. Nada é gravado antes do
 * "Importar". Só cria produto: o que já está cadastrado continua como está.
 */
import { computed, ref, watch } from 'vue';
import { useQueryClient } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import { AlertTriangle, CheckCircle2, FileSpreadsheet } from 'lucide-vue-next';

import BaseModal from '@/shared/components/commons/BaseModal/BaseModal.vue';
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import { useToast } from '@/shared/composables/useToast';
import { getErrorMessage } from '@/shared/utils/error.utils';
import type { ApiError } from '@/shared/types/axios.types';
import { formatCurrency } from '@/shared/utils/finance';
import { PRODUTOS_QUERY_KEY } from '@/modules/products/shared/constants/queryKeys';
import { MOVIMENTACOES_QUERY_KEY } from '../composables/useMovimentacoesQuery';
import { importarPlanilha, lerPlanilha } from '../services/importacaoPlanilha.service';
import type {
  PreviaImportacao,
  ResultadoImportacaoPlanilha,
  SituacaoLinha,
} from '../types/importacaoPlanilha.types';

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{ close: [] }>();

const toast = useToast();
const queryClient = useQueryClient();

const etapa = ref<'arquivo' | 'conferencia' | 'pronto'>('arquivo');
const arquivo = ref<File | null>(null);
const previa = ref<PreviaImportacao | null>(null);
const resultado = ref<ResultadoImportacaoPlanilha | null>(null);
const lendo = ref(false);
const importando = ref(false);
const arrastando = ref(false);
const filtro = ref<SituacaoLinha | 'todos'>('todos');

// A tabela mostra um pedaço por vez: centenas de linhas travariam a janela à toa.
const LIMITE_NA_TELA = 200;

const ROTULOS: Record<SituacaoLinha, string> = {
  novo: 'Novo',
  existe: 'Já cadastrado',
  ignorado: 'Não importar',
  erro: 'Com erro',
};

const filtros = computed(() => {
  const p = previa.value;
  if (!p) return [];
  return [
    { valor: 'todos' as const, rotulo: 'Todos', quantidade: p.linhas.length },
    { valor: 'novo' as const, rotulo: 'Novos', quantidade: p.novos },
    { valor: 'erro' as const, rotulo: 'Com erro', quantidade: p.com_erro },
    { valor: 'existe' as const, rotulo: 'Já cadastrados', quantidade: p.ja_existem },
    { valor: 'ignorado' as const, rotulo: 'Não importar', quantidade: p.ignorados },
  ];
});

const linhasFiltradas = computed(() => {
  const linhas = previa.value?.linhas ?? [];
  return filtro.value === 'todos' ? linhas : linhas.filter((l) => l.situacao === filtro.value);
});

const fiscalVaiFicarDeFora = computed(() => !!previa.value?.planilha_tem_fiscal && !previa.value.fiscal_disponivel);

function recomecar() {
  etapa.value = 'arquivo';
  arquivo.value = null;
  previa.value = null;
  resultado.value = null;
  filtro.value = 'todos';
}

watch(() => props.isOpen, (aberto) => {
  if (aberto) recomecar();
});

async function lerArquivo(escolhido: File | undefined) {
  if (!escolhido) return;
  lendo.value = true;
  try {
    previa.value = await lerPlanilha(escolhido);
    arquivo.value = escolhido;
    filtro.value = 'todos';
    etapa.value = 'conferencia';
  } catch (erro) {
    toast.error('Não foi possível ler a planilha', getErrorMessage(erro as AxiosError<ApiError>, 'Confira se o arquivo é um Excel .xlsx.'));
  } finally {
    lendo.value = false;
  }
}

function aoEscolher(evento: Event) {
  const input = evento.target as HTMLInputElement;
  lerArquivo(input.files?.[0]);
  input.value = '';
}

function aoSoltar(evento: DragEvent) {
  arrastando.value = false;
  lerArquivo(evento.dataTransfer?.files?.[0]);
}

async function confirmar() {
  if (!arquivo.value) return;
  importando.value = true;
  try {
    resultado.value = await importarPlanilha(arquivo.value);
    etapa.value = 'pronto';
    queryClient.invalidateQueries({ queryKey: [PRODUTOS_QUERY_KEY] });
    queryClient.invalidateQueries({ queryKey: [MOVIMENTACOES_QUERY_KEY] });
    toast.success(`${resultado.value.criados} produtos importados`);
  } catch (erro) {
    toast.error('A importação não foi feita', getErrorMessage(erro as AxiosError<ApiError>, 'Nada foi gravado. Confira e tente de novo.'));
  } finally {
    importando.value = false;
  }
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Importar produtos por planilha"
    :subtitle="arquivo ? arquivo.name : 'Cadastre vários produtos de uma vez'"
    :size="etapa === 'conferencia' ? '4xl' : 'lg'"
    @close="emit('close')"
  >
    <!-- Passo 1: arquivo -->
    <div v-if="etapa === 'arquivo'" class="space-y-4">
      <label
        class="flex flex-col items-center justify-center gap-3 p-10 border-2 border-dashed rounded-2xl cursor-pointer transition-colors"
        :class="arrastando ? 'border-brand-primary bg-brand-primary/5' : 'border-zinc-300 hover:border-brand-primary/60'"
        @dragover.prevent="arrastando = true"
        @dragleave.prevent="arrastando = false"
        @drop.prevent="aoSoltar"
      >
        <FileSpreadsheet :size="36" class="text-brand-primary" />
        <span class="text-sm font-semibold text-zinc-700">
          {{ lendo ? 'Lendo a planilha…' : 'Escolha ou arraste a planilha Excel (.xlsx)' }}
        </span>
        <input
          type="file"
          accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          class="hidden"
          :disabled="lendo"
          @change="aoEscolher"
        />
      </label>
      <div class="text-xs text-zinc-500 space-y-1">
        <p>
          A primeira linha precisa ter os títulos <strong>CODIGO</strong>, <strong>NOME</strong> e
          <strong>PRECO_VENDA</strong>. Também podem vir UNIDADE, CODIGO_BARRAS, CATEGORIA, NCM, CFOP, CSOSN, CUSTO,
          ESTOQUE e IMPORTAR (SIM ou NAO).
        </p>
        <p>Nada é gravado agora: primeiro você confere a lista, depois confirma.</p>
      </div>
    </div>

    <!-- Passo 2: conferência -->
    <div v-else-if="etapa === 'conferencia' && previa" class="space-y-4">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="f in filtros"
          :key="f.valor"
          type="button"
          class="px-3 py-1.5 rounded-full border text-xs font-semibold transition-colors"
          :class="filtro === f.valor ? 'bg-brand-primary text-white border-brand-primary' : 'bg-white text-zinc-600 border-zinc-300 hover:border-brand-primary/60'"
          @click="filtro = f.valor"
        >
          {{ f.rotulo }}: {{ f.quantidade }}
        </button>
      </div>

      <p v-if="fiscalVaiFicarDeFora" class="flex gap-2 p-3 rounded-lg bg-amber-50 border border-amber-300 text-xs text-amber-900">
        <AlertTriangle :size="16" class="shrink-0" />
        <span>
          O fiscal desta loja ainda não está configurado, então <strong>NCM, CFOP e CSOSN da planilha não serão gravados</strong>.
          Para trazê-los, configure o fiscal antes de importar.
        </span>
      </p>

      <div class="overflow-x-auto border border-zinc-200 rounded-xl max-h-[50vh]">
        <table class="w-full text-xs">
          <thead class="bg-zinc-50 text-zinc-500 sticky top-0">
            <tr class="text-left">
              <th class="px-3 py-2 font-semibold">Linha</th>
              <th class="px-3 py-2 font-semibold">Código</th>
              <th class="px-3 py-2 font-semibold">Produto</th>
              <th class="px-3 py-2 font-semibold">NCM</th>
              <th class="px-3 py-2 font-semibold text-right">Custo</th>
              <th class="px-3 py-2 font-semibold text-right">Preço</th>
              <th class="px-3 py-2 font-semibold text-right">Estoque</th>
              <th class="px-3 py-2 font-semibold">Situação</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in linhasFiltradas.slice(0, LIMITE_NA_TELA)" :key="l.linha" class="border-t border-zinc-100 align-top">
              <td class="px-3 py-2 text-zinc-400">{{ l.linha }}</td>
              <td class="px-3 py-2 text-zinc-600">{{ l.codigo }}</td>
              <td class="px-3 py-2 text-zinc-800">
                {{ l.nome }}
                <span
                  v-for="(m, i) in l.mensagens"
                  :key="i"
                  class="block text-[11px]"
                  :class="l.situacao === 'erro' ? 'text-red-600' : 'text-amber-700'"
                >{{ m }}</span>
              </td>
              <td class="px-3 py-2 text-zinc-600">{{ l.ncm || '—' }}</td>
              <td class="px-3 py-2 text-right text-zinc-600 whitespace-nowrap">{{ l.custo != null ? formatCurrency(l.custo) : '—' }}</td>
              <td class="px-3 py-2 text-right text-zinc-800 whitespace-nowrap">{{ l.preco != null ? formatCurrency(l.preco) : '—' }}</td>
              <td class="px-3 py-2 text-right text-zinc-600">{{ l.estoque.toLocaleString('pt-BR') }}</td>
              <td class="px-3 py-2 whitespace-nowrap font-semibold" :class="{
                'text-emerald-700': l.situacao === 'novo',
                'text-red-600': l.situacao === 'erro',
                'text-zinc-500': l.situacao === 'existe' || l.situacao === 'ignorado',
              }">{{ ROTULOS[l.situacao] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="linhasFiltradas.length > LIMITE_NA_TELA" class="text-[11px] text-zinc-500">
        Mostrando {{ LIMITE_NA_TELA }} de {{ linhasFiltradas.length }} linhas. Use os filtros para ver as outras.
      </p>
    </div>

    <!-- Passo 3: resumo -->
    <div v-else-if="etapa === 'pronto' && resultado" class="flex flex-col items-center gap-3 py-6 text-center">
      <CheckCircle2 :size="40" class="text-emerald-600" />
      <p class="text-base font-semibold text-zinc-800">{{ resultado.criados }} produtos importados</p>
      <p class="text-xs text-zinc-500">
        {{ resultado.ja_existiam }} já estavam cadastrados, {{ resultado.ignorados }} marcados para não importar e
        {{ resultado.com_erro }} com erro ficaram de fora.
      </p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-3">
        <template v-if="etapa === 'conferencia'">
          <BaseButton variant="secondary" @click="recomecar">Outro arquivo</BaseButton>
          <BaseButton :disabled="importando || !previa?.novos" :is-loading="importando" @click="confirmar">
            Importar {{ previa?.novos ?? 0 }} produtos
          </BaseButton>
        </template>
        <BaseButton v-else-if="etapa === 'pronto'" variant="secondary" @click="emit('close')">Fechar</BaseButton>
        <BaseButton v-else variant="secondary" @click="emit('close')">Cancelar</BaseButton>
      </div>
    </template>
  </BaseModal>
</template>
