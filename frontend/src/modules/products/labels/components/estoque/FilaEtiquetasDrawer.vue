<script setup lang="ts">
/**
 * @fileoverview A fila de impressão, num painel que abre da direita: modelo,
 * preview e os produtos com a quantidade de etiquetas de cada um.
 *
 * Painel (e não coluna fixa da aba) para o catálogo ficar com a largura toda.
 * Mesmo padrão visual do `TransacoesEstoquePanel` do Estoque.
 */
import { computed } from 'vue';
import { Printer, Trash2, X, Settings2, Ruler, Tags, AlertTriangle, MousePointer2 } from 'lucide-vue-next';

import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue';
import BaseSelect from '@/shared/components/ui/BaseSelect/BaseSelect.vue';
import BaseInput from '@/shared/components/ui/BaseInput/BaseInput.vue';
import EtiquetaPreview from '@/shared/etiquetas/components/EtiquetaPreview.vue';
import { etiquetasPorPagina, type ModeloEtiqueta } from '@/shared/etiquetas/modelo';
import { VALORES_EXEMPLO } from '@/shared/etiquetas/campos';
import { MAX_POR_ITEM } from '../../store/filaEtiquetas.store';
import type { LinhaFila } from '../../types/etiquetas.types';

const props = defineProps<{
  isOpen: boolean;
  linhas: LinhaFila[];
  modelos: ModeloEtiqueta[];
  modelo: ModeloEtiqueta;
  totalEtiquetas: number;
}>();

const emit = defineEmits<{
  close: [];
  'update:quantidade': [produtoId: number, quantidade: number];
  remover: [produtoId: number];
  limpar: [];
  imprimir: [];
  imprimirTeste: [];
  gerenciarModelos: [];
  editarLayout: [];
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
  const base = ehFolha.value
    ? `Folha · ${medida} · ${porPagina.value} por folha`
    : `Rolo · ${medida} · ${p.colunas} ${p.colunas === 1 ? 'coluna' : 'colunas'}`;
  return props.modelo.descricao ? `${base} · ${props.modelo.descricao}` : base;
});

const folhas = computed(() => {
  if (!ehFolha.value || props.totalEtiquetas === 0) return 0;
  return Math.ceil((props.totalEtiquetas + pular.value) / porPagina.value);
});

const valoresPreview = computed(() => props.linhas[0]?.valores ?? VALORES_EXEMPLO);
const semCodigo = computed(() => props.linhas.filter((l) => l.semCodigo));
</script>

<template>
  <Teleport to="body">
    <Transition name="panel">
      <div v-if="isOpen" class="fixed inset-0 z-40 flex justify-end">
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" @click="emit('close')" />

        <div class="relative z-50 w-full max-w-lg bg-white shadow-2xl flex flex-col h-full">
          <!-- Cabeçalho -->
          <div class="flex items-center justify-between gap-3 px-6 py-4 border-b border-zinc-100 shrink-0">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-xl bg-brand-primary/10 text-brand-primary flex items-center justify-center">
                <Tags :size="18" />
              </div>
              <div>
                <h2 class="text-lg font-semibold text-zinc-800">Fila de impressão</h2>
                <p class="text-xs text-zinc-400">
                  {{ totalEtiquetas }} {{ totalEtiquetas === 1 ? 'etiqueta' : 'etiquetas' }}
                  <template v-if="folhas"> · {{ folhas }} {{ folhas === 1 ? 'folha' : 'folhas' }}</template>
                </p>
              </div>
            </div>
            <div class="flex items-center gap-1">
              <button
                v-if="linhas.length"
                class="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs font-medium text-zinc-500 hover:text-red-600 hover:bg-red-50 cursor-pointer"
                @click="emit('limpar')"
              >
                <Trash2 :size="14" />
                Limpar
              </button>
              <button
                class="p-2 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors cursor-pointer"
                title="Fechar"
                @click="emit('close')"
              >
                <X :size="20" />
              </button>
            </div>
          </div>

          <!-- Conteúdo -->
          <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
            <!-- Modelo -->
            <div class="space-y-2">
              <div class="flex items-end gap-2">
                <BaseSelect v-model="chaveModelo" :options="opcoesModelo" label="Modelo de etiqueta" class="flex-1" />
                <button
                  class="h-11 w-11 shrink-0 flex items-center justify-center rounded-lg border border-zinc-200 text-zinc-500 hover:text-brand-primary hover:border-brand-primary cursor-pointer"
                  title="Criar e editar modelos da loja"
                  @click="emit('gerenciarModelos')"
                >
                  <Settings2 :size="18" />
                </button>
                <button
                  class="h-11 w-11 shrink-0 flex items-center justify-center rounded-lg border border-zinc-200 text-zinc-500 hover:text-brand-primary hover:border-brand-primary cursor-pointer"
                  title="Calibrar a impressão neste computador"
                  @click="emit('calibrar')"
                >
                  <Ruler :size="18" />
                </button>
              </div>
              <div class="flex flex-wrap items-center justify-between gap-2">
                <p class="text-xs text-zinc-500">{{ resumoPapel }}</p>
                <button
                  type="button"
                  class="flex items-center gap-1 text-xs font-semibold text-brand-primary hover:underline cursor-pointer"
                  :title="modelo.id ? 'Abrir este modelo no editor visual' : 'Modelo pronto não se altera: abre uma cópia no editor visual'"
                  @click="emit('editarLayout')"
                >
                  <MousePointer2 :size="13" />
                  Editar layout
                </button>
              </div>
            </div>

            <!-- Preview -->
            <div class="flex flex-col items-center gap-2 rounded-xl bg-zinc-50 border border-zinc-100 p-4">
              <EtiquetaPreview :definicao="modelo.definicao" :valores="valoresPreview" :largura-max-px="360" />
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
            <div>
              <h3 class="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-2">Produtos na fila</h3>
              <div v-if="linhas.length" class="divide-y divide-zinc-100 border border-zinc-100 rounded-xl">
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
              <p v-else class="text-sm text-zinc-400 text-center py-6 px-4 border border-dashed border-zinc-200 rounded-xl">
                A fila está vazia. Adicione produtos pela lista, pelas <strong>Entradas recentes</strong> ou pelo botão
                <strong>Etiqueta</strong> no card do produto.
              </p>
            </div>
          </div>

          <!-- Ações -->
          <div class="flex gap-2 px-6 py-4 border-t border-zinc-100 shrink-0">
            <BaseButton variant="ghost" class="flex items-center justify-center gap-2 flex-1" @click="emit('imprimirTeste')">
              <Ruler :size="16" />
              Imprimir teste
            </BaseButton>
            <BaseButton
              variant="primary"
              class="flex items-center justify-center gap-2 flex-2"
              :disabled="totalEtiquetas === 0"
              @click="emit('imprimir')"
            >
              <Printer :size="16" />
              Imprimir {{ totalEtiquetas || '' }} {{ totalEtiquetas === 1 ? 'etiqueta' : 'etiquetas' }}
            </BaseButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.2s ease;
}
.panel-enter-from,
.panel-leave-to {
  opacity: 0;
}
.panel-enter-active > div:last-child,
.panel-leave-active > div:last-child {
  transition: transform 0.25s ease;
}
.panel-enter-from > div:last-child,
.panel-leave-to > div:last-child {
  transform: translateX(100%);
}
</style>
