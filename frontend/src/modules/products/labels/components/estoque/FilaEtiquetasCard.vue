<script setup lang="ts">
/**
 * @fileoverview A fila de impressão: modelo, preview e os produtos com a
 * quantidade de etiquetas de cada um.
 */
import { computed } from 'vue';
import { Printer, Trash2, X, Settings2, Ruler, Tags, AlertTriangle } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import EtiquetaPreview from '@/shared/etiquetas/components/EtiquetaPreview.vue';
import { etiquetasPorPagina, type ModeloEtiqueta } from '@/shared/etiquetas/modelo';
import { VALORES_EXEMPLO } from '@/shared/etiquetas/campos';
import { MAX_POR_ITEM } from '../../store/filaEtiquetas.store';
import type { LinhaFila } from '../../types/etiquetas.types';

const props = defineProps<{
  linhas: LinhaFila[];
  modelos: ModeloEtiqueta[];
  modelo: ModeloEtiqueta;
  totalEtiquetas: number;
}>();

const emit = defineEmits<{
  'update:quantidade': [produtoId: number, quantidade: number];
  remover: [produtoId: number];
  limpar: [];
  imprimir: [];
  imprimirTeste: [];
  gerenciarModelos: [];
  calibrar: [];
}>();

const chaveModelo = defineModel<string>('chaveModelo', { required: true });
const pular = defineModel<number>('pular', { required: true });

const opcoesModelo = computed(() =>
  props.modelos.map((m) => ({ value: m.chave, label: m.id ? `${m.nome} (da loja)` : m.nome })),
);

const pagina = computed(() => props.modelo.definicao.pagina);
const ehFolha = computed(() => pagina.value.tipo === 'folha');
const porPagina = computed(() => etiquetasPorPagina(pagina.value));

const resumoPapel = computed(() => {
  const p = pagina.value;
  const medida = `${p.largura_mm.toLocaleString('pt-BR')} × ${p.altura_mm.toLocaleString('pt-BR')} mm`;
  if (!ehFolha.value) return `Rolo · ${medida} · ${p.colunas} ${p.colunas === 1 ? 'coluna' : 'colunas'}`;
  return `Folha · ${medida} · ${porPagina.value} por folha`;
});

const folhas = computed(() => {
  if (!ehFolha.value || props.totalEtiquetas === 0) return 0;
  return Math.ceil((props.totalEtiquetas + pular.value) / porPagina.value);
});

const valoresPreview = computed(() => props.linhas[0]?.valores ?? VALORES_EXEMPLO);
const semCodigo = computed(() => props.linhas.filter((l) => l.semCodigo));
</script>

<template>
  <div class="bg-white rounded-2xl p-5 space-y-5">
    <!-- Cabeçalho -->
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <div class="w-9 h-9 rounded-xl bg-brand-primary/10 text-brand-primary flex items-center justify-center">
          <Tags :size="18" />
        </div>
        <div>
          <h3 class="text-sm font-bold text-zinc-800">Fila de impressão</h3>
          <p class="text-xs text-zinc-500">
            {{ totalEtiquetas }} {{ totalEtiquetas === 1 ? 'etiqueta' : 'etiquetas' }}
            <template v-if="folhas"> · {{ folhas }} {{ folhas === 1 ? 'folha' : 'folhas' }}</template>
          </p>
        </div>
      </div>
      <button
        v-if="linhas.length"
        class="flex items-center gap-1 text-xs font-medium text-zinc-500 hover:text-red-600 cursor-pointer"
        @click="emit('limpar')"
      >
        <Trash2 :size="14" />
        Limpar
      </button>
    </div>

    <!-- Modelo -->
    <div class="space-y-2">
      <div class="flex items-end gap-2">
        <BaseSelect v-model="chaveModelo" :options="opcoesModelo" label="Modelo de etiqueta" class="flex-1" />
        <button
          class="h-11 w-11 flex items-center justify-center rounded-lg border border-zinc-200 text-zinc-500 hover:text-brand-primary hover:border-brand-primary cursor-pointer"
          title="Criar e editar modelos da loja"
          @click="emit('gerenciarModelos')"
        >
          <Settings2 :size="18" />
        </button>
        <button
          class="h-11 w-11 flex items-center justify-center rounded-lg border border-zinc-200 text-zinc-500 hover:text-brand-primary hover:border-brand-primary cursor-pointer"
          title="Calibrar a impressão neste computador"
          @click="emit('calibrar')"
        >
          <Ruler :size="18" />
        </button>
      </div>
      <p class="text-xs text-zinc-500">{{ resumoPapel }}<template v-if="modelo.descricao"> · {{ modelo.descricao }}</template></p>
    </div>

    <!-- Preview -->
    <div class="flex flex-col items-center gap-2 rounded-xl bg-zinc-50 border border-zinc-100 p-4">
      <EtiquetaPreview :definicao="modelo.definicao" :valores="valoresPreview" />
      <span class="text-[11px] text-zinc-400">
        {{ linhas.length ? 'Primeira etiqueta da fila' : 'Exemplo — adicione produtos para ver os seus' }}
      </span>
    </div>

    <BaseInput
      v-if="ehFolha"
      v-model.number="pular"
      type="number"
      :min="0"
      :max="porPagina - 1"
      label="Pular posições na primeira folha"
      ajuda="Folha já usada? Informe quantas etiquetas já foram arrancadas, contando da esquerda para a direita, de cima para baixo."
    />

    <!-- Avisos -->
    <div
      v-if="semCodigo.length"
      class="flex items-start gap-2 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900"
    >
      <AlertTriangle :size="15" class="shrink-0 mt-0.5" />
      <span>
        {{ semCodigo.length === 1 ? 'Um produto não tem' : `${semCodigo.length} produtos não têm` }}
        código de barras nem código interno — a etiqueta sai sem barras:
        <strong>{{ semCodigo.map((l) => l.produto.nome).join(', ') }}</strong>.
      </span>
    </div>

    <!-- Itens -->
    <div v-if="linhas.length" class="divide-y divide-zinc-100 border border-zinc-100 rounded-xl max-h-80 overflow-y-auto">
      <div v-for="linha in linhas" :key="linha.produto.id" class="flex items-center gap-3 px-3 py-2">
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-zinc-800 truncate">{{ linha.produto.nome }}</p>
          <p class="text-xs text-zinc-400 font-mono truncate">
            {{ linha.produto.codigo_barras || linha.produto.codigo_produto || 'sem código' }}
          </p>
        </div>
        <input
          type="number"
          min="1"
          :max="MAX_POR_ITEM"
          :value="linha.quantidade"
          class="w-20 px-2 py-1.5 text-sm text-right border border-zinc-200 rounded-lg focus:outline-none focus:border-brand-primary"
          title="Quantidade de etiquetas"
          @change="emit('update:quantidade', linha.produto.id, Number(($event.target as HTMLInputElement).value))"
        />
        <button
          class="p-1.5 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 cursor-pointer"
          title="Tirar da fila"
          @click="emit('remover', linha.produto.id)"
        >
          <X :size="16" />
        </button>
      </div>
    </div>
    <p v-else class="text-sm text-zinc-400 text-center py-6 border border-dashed border-zinc-200 rounded-xl">
      Adicione produtos pela lista ao lado, pelas entradas recentes<br />ou pelo botão <strong>Etiqueta</strong> no card do produto.
    </p>

    <!-- Ações -->
    <div class="flex flex-col sm:flex-row gap-2">
      <BaseButton variant="ghost" class="flex items-center justify-center gap-2 sm:flex-1" @click="emit('imprimirTeste')">
        <Ruler :size="16" />
        Imprimir teste
      </BaseButton>
      <BaseButton
        variant="primary"
        class="flex items-center justify-center gap-2 sm:flex-[2]"
        :disabled="totalEtiquetas === 0"
        @click="emit('imprimir')"
      >
        <Printer :size="16" />
        Imprimir {{ totalEtiquetas || '' }} {{ totalEtiquetas === 1 ? 'etiqueta' : 'etiquetas' }}
      </BaseButton>
    </div>
  </div>
</template>
